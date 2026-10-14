import re
import pymupdf

SECTION_RE = re.compile(
    r"^\s*(?:\d+(?:\.\d+)*\.?\s+|[IVX]+\.\s+)?"
    r"(abstract|introduction|related work|background|methods?|methodology|approach|"
    r"experiments?|results?|evaluation|discussion|limitations?|conclusions?|"
    r"future work|applications?|case study|references|bibliography|appendix|appendices)\b.*$",
    re.IGNORECASE,
)

# Task 4.2: PDF Extraction & Cleaning
def _mostly_inside(rect, rects, frac=0.6):
    area = rect.get_area()
    return area > 0 and any((rect & r).get_area() / area >= frac for r in rects)


def _order_blocks(blocks, W):
    """Full-width blocks act as separators; between them read left col, then right col."""
    full = sorted([b for b in blocks if b[0].width > 0.6 * W], key=lambda b: b[0].y0)
    cols = [b for b in blocks if b[0].width <= 0.6 * W]
    ordered, prev = [], -1.0
    for y, fb in [(b[0].y0, b) for b in full] + [(1e9, None)]:
        band = [b for b in cols if prev <= b[0].y0 < y]
        mid = lambda b: (b[0].x0 + b[0].x1) / 2
        ordered += sorted([b for b in band if mid(b) < W / 2], key=lambda b: b[0].y0)
        ordered += sorted([b for b in band if mid(b) >= W / 2], key=lambda b: b[0].y0)
        if fb:
            ordered.append(fb)
            prev = y
    return ordered


NUMERIC_CHARS = set("0123456789.±%+-−,")

def _numeric_ratio(s: str) -> float:
    s = s.replace(" ", "")
    return sum(c in NUMERIC_CHARS for c in s) / len(s) if s else 0.0

def extract_pages(pdf_path: str) -> list[dict]:
    doc = pymupdf.open(pdf_path)
    pages = []
    for page_num, page in enumerate(doc, start=1):
        W, H = page.rect.width, page.rect.height

        # Regions to ignore: raster images, vector charts, tables
        skip = [pymupdf.Rect(i["bbox"]) for i in page.get_image_info()]
        try:
            skip += [r for r in page.cluster_drawings() if r.width > 60 and r.height > 60]
        except Exception:
            pass
        try:
            skip += [pymupdf.Rect(t.bbox) for t in page.find_tables().tables]
        except Exception:
            pass
        skip = [r for r in skip if r.get_area() < 0.7 * W * H]  # ignore page-sized boxes

        blocks = []
        for x0, y0, x1, y1, text, _, btype in page.get_text("blocks"):
            if btype != 0:                       # not a text block
                continue
            rect, text = pymupdf.Rect(x0, y0, x1, y1), text.strip()
            if not text or rect.y1 < 0.05 * H or rect.y0 > 0.95 * H:   # headers/footers
                continue
            is_caption = re.match(r"(Figure|Fig\.|Table)\s*\d+", text)
            if not is_caption and _mostly_inside(rect, skip):
                continue

            text = re.sub(r"-\n(?=[a-z])", "", text)        # de-hyphenate
            out, para, prev_num = [], [], None

            def flush():
                if para:
                    out.append(" ".join(para))
                    para.clear()

            for l in (x.strip() for x in text.split("\n")):
                if not l:
                    continue
                if re.fullmatch(r"(\d+(?:\.\d+)*\.?|[IVX]+\.?)", l):   # lone "1" / "2.1"
                    prev_num = l
                    continue
                cand = f"{prev_num} {l}" if prev_num else l
                prev_num = None
                if len(cand) < 60 and SECTION_RE.match(cand):
                    flush()
                    out.append(cand)                         # heading on its own line
                    continue
                if not is_caption and (len(l) <= 3 or _numeric_ratio(l) >= 0.35):
                    continue
                para.append(l)
            flush()

            text = re.sub(r"[ \t]+", " ", "\n".join(out)).strip()
            if not text:
                continue
            if len(text) < 40 and not is_caption and not SECTION_RE.match(text):
                continue
            blocks.append((rect, text))



        page_text = "\n\n".join(t for _, t in _order_blocks(blocks, W))
        page_text = re.sub(r"arXiv:\d{4}\.\d{4,5}(v\d+)?\s*\[.*?\]\s*\d{1,2}\s+\w+\s+\d{4}", "", page_text)
        if page_text.strip():
            pages.append({"page": page_num, "text": page_text.strip()})
    doc.close()
    return pages


def split_into_sections(pages: list[dict]) -> tuple[list[dict], list[tuple[int, int]]]:
    """Return [{section, text, page_spans}], dropping references onward."""
    # Build one document string, tracking where each page starts
    full, offsets, pos = [], [], 0
    for p in pages:
        offsets.append((pos, p["page"]))
        full.append(p["text"])
        pos += len(p["text"]) + 2
    doc_text = "\n\n".join(full)

    # Find headings: short standalone lines matching known section names
    heads = []
    for m in re.finditer(r"^.+$", doc_text, flags=re.MULTILINE):
        line = m.group(0)
        if len(line) < 60 and (s := SECTION_RE.match(line)):
            section_name = s.group(1).lower()
            if section_name == "appendices":
                section_name = "appendix"
            heads.append((m.start(), section_name))

    sections, start, name = [], 0, "front_matter"
    for h_start, h_name in heads + [(len(doc_text), "end")]:
        if h_start > start:
            sections.append({"section": name, "start": start, "end": h_start})
        start, name = h_start, h_name
    # Cut at references, bibliography, or appendix
    out = []
    for s in sections:
        if s["section"] in ["references", "bibliography", "appendix"]:
            break
        out.append({**s, "text": doc_text[s["start"]:s["end"]]})
    return out, offsets


def page_for(offset: int, offsets: list[tuple[int, int]]) -> int:
    page = offsets[0][1]
    for start, num in offsets:
        if start <= offset:
            page = num
        else:
            break
    return page

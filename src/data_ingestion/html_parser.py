import re
from bs4 import BeautifulSoup

SKIP_CHAPTERS = ("acknowledg", "contents", "list of", "bibliograph",
                 "references", "dedication", "declaration")

def parse_html_sections(html: str) -> list[dict]:
    """arXiv/LaTeXML HTML -> [{section, subsection, text}] with no heading guessing."""
    out = []
    soup = BeautifulSoup(html, "html.parser")

    # keep figure/table captions, drop the figure/table bodies
    for fig in soup.select("figure"):
        cap = fig.find("figcaption")
        fig.replace_with(cap) if cap else fig.decompose()
    # drop references, appendices, display equations, proofs, section numbers, nav
    for t in soup.select(".ltx_bibliography, .ltx_appendix, .ltx_equation, .ltx_equationgroup, "
                         ".ltx_proof, .ltx_tag, nav"):
        t.decompose()
    # inline math -> its LaTeX alt text
    for m in soup.find_all("math"):
        m.replace_with(m.get("alttext", ""))

    abs_ = soup.select_one("div.ltx_abstract")
    if abs_:
        for t in abs_.select(".ltx_title"):          # drop the "Abstract" label
            t.decompose()
        out.append({"section": "abstract", "subsection": "",
                    "text": abs_.get_text(" ", strip=True)})
        abs_.decompose()                              # avoid emitting it twice    

    def paras(node, recursive):
        return " ".join(
            p.get_text(" ", strip=True)
            for p in node.find_all(["div", "p"], class_=["ltx_para", "ltx_caption"], recursive=recursive)
        )


    def title(node):
        h = (node.find(re.compile(r"^h[1-6]$"), class_="ltx_title", recursive=False)
            or node.find(re.compile(r"^h[1-6]$"), class_="ltx_title"))
        name = h.get_text(" ", strip=True).lower() if h else ""
        return re.sub(r"^chapter\s+\d+\s*", "", name)
 
    def emit(top, sub, node, recursive):
        if text := paras(node, recursive):
            out.append({"section": top, "subsection": sub, "text": text})

    chapters = soup.select("section.ltx_chapter")
    if chapters:                                      # thesis / book class
        for ch in chapters:
            top = title(ch)
            if top.startswith(SKIP_CHAPTERS):
                continue
            emit(top, "", ch, False)
            for sec in ch.find_all("section", class_="ltx_section", recursive=False):
                emit(top, title(sec), sec, True)
    else:                                             # normal paper
        for sec in soup.select("section.ltx_section"):
            top = title(sec)
            emit(top, "", sec, False)
            for sub in sec.find_all("section", class_="ltx_subsection", recursive=False):
                emit(top, title(sub), sub, True)

    return out
from pathlib import Path
import tempfile
import argparse
import json
import tarfile
import pandas as pd

from . import config as cfg
from .metadata import load_metadata
from .download import download_pdfs, download_html, load_html, resolve_pdf_path
from .html_parser import parse_html_sections
from .pdf_parser import extract_pages
from .chunking import chunk_html_sections, chunk_document
from .tex_figures import extract_figure_text
from .tex_source import MAX_ARCHIVE, cache_path, chunk_source, download_sources


# Task 4.4: Deduplication & Storage
def process_and_store(
    metadata_list: list[dict],
    output_path: Path | None = None,
    *, use_tex: bool = False, use_tex_figures: bool = False,
) -> pd.DataFrame:
    """Publish only a complete corpus; preserve the previous output on failure."""
    if use_tex_figures and not use_tex:
        raise ValueError('Figure extraction requires use_tex=True')
    if not metadata_list:
        raise ValueError("No papers selected for ingestion")
    output_path = Path(output_path) if output_path is not None else cfg.PROCESSED_DIR / "chunks.parquet"
    df_meta = pd.DataFrame(metadata_list)

    # Recognize newer paper versions by base ID and keep latest updated
    df_meta["base_arxiv_id"] = df_meta["arxiv_id"].str.replace(r"v\d+$", "", regex=True)
    df_latest = (
        df_meta.sort_values("updated")
        .drop_duplicates("base_arxiv_id", keep="last")
        .reset_index(drop=True)
    )

    all_chunks = []
    failures = []
    for _, row in df_latest.iterrows():
        aid, chunks, source = row["arxiv_id"], [], None

        # 1) HTML first
        html = load_html(aid)
        if html:
            try:
                chunks = chunk_html_sections(parse_html_sections(html), aid, row["title"])
                source = "html"
            except Exception as e:
                print(f"[HTML parse failed] {aid}: {e}")

        # Opt-in TeX fallback: never compile or pretend source lines are PDF pages.
        if not chunks and use_tex:
            try:
                path = cache_path(aid)
                if path.exists():
                    with path.open("rb") as stream:
                        data = stream.read(MAX_ARCHIVE + 1)
                        chunks = chunk_source(data, aid, row["title"])
                    if use_tex_figures:
                        figures = extract_figure_text(data, aid, row["title"])
                        chunks.extend(figures["chunks"])
                        for chunk in chunks:
                            chunk["figure_coverage"] = json.dumps(figures["coverage"], sort_keys=True)
                    source = "tex"
            except (OSError, ValueError, EOFError, tarfile.TarError) as error:
                chunks = []
                print(f"[TeX unavailable] {aid}: {error}")

        # PDF fallback only when higher-priority sources produced no chunks.
        if not chunks:
            pdf_path = resolve_pdf_path(aid)
            if pdf_path is None:
                reason = "no usable HTML or local PDF" if not use_tex else "no usable HTML, TeX, or local PDF"
                failures.append(f"{aid}: {reason}")
                continue
            try:
                pages = extract_pages(str(pdf_path))
                chunks = chunk_document(pages, aid, row["title"])
                if not chunks:
                    raise ValueError("no extractable text; check whether OCR is needed")
                source = "pdf"
            except Exception as e:
                print(f"[PDF failed] {aid}: {e}")
                failures.append(f"{aid}: {e}")
                continue

        print(f"[{source}] {aid}: {len(chunks)} chunks")
        for c in chunks:
            c.update({
                "source": c.get("source", source),
                "title": row["title"],
                "categories": row["categories"],
                "authors": row["authors"],
                "abstract": row["abstract"],
                "published": row["published"],
                "updated": row["updated"],
                "pdf_url": row["pdf_url"],
            })
            all_chunks.append(c)

    if failures:
        raise RuntimeError("Incomplete ingestion; output was not replaced: " + "; ".join(failures))

    df_out = pd.DataFrame(all_chunks)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output_path.parent, suffix=".parquet", delete=False) as file:
        temporary_path = Path(file.name)
    try:
        df_out.to_parquet(temporary_path, index=False)
        temporary_path.replace(output_path)
    finally:
        temporary_path.unlink(missing_ok=True)
    print(f"Saved {len(df_out)} chunks from {df_out['arxiv_id'].nunique()} papers to {output_path}")
    print(df_out.groupby("source")["arxiv_id"].nunique())
    return df_out


def main():
    parser = argparse.ArgumentParser(description="HTML/PDF ingestion with opt-in raw TeX fallback")
    parser.add_argument('--with-tex', action='store_true', help='Download and use raw TeX between HTML and PDF')
    parser.add_argument('--with-tex-figures', action='store_true',
                        help='Add bundled figure-PDF text and coverage records (requires --with-tex)')
    args = parser.parse_args()
    if args.with_tex_figures and not args.with_tex:
        parser.error('--with-tex-figures requires --with-tex')
    metadata = load_metadata()
    if args.with_tex:
        download_sources(metadata)
    download_pdfs(metadata)       # fallback source
    download_html(metadata)       # skips cached, remembers 404s
    process_and_store(metadata, use_tex=args.with_tex, use_tex_figures=args.with_tex_figures)


if __name__ == "__main__":
    main()

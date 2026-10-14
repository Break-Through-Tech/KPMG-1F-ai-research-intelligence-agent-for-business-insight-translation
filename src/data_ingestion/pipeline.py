from pathlib import Path
import tempfile
import pandas as pd

from . import config as cfg
from .metadata import load_metadata
from .download import download_pdfs, download_html, load_html, resolve_pdf_path
from .html_parser import parse_html_sections
from .pdf_parser import extract_pages
from .chunking import chunk_html_sections, chunk_document


# Task 4.4: Deduplication & Storage
def process_and_store(
    metadata_list: list[dict],
    output_path: Path | None = None,
) -> pd.DataFrame:
    """Publish only a complete corpus; preserve the previous output on failure."""
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

        # 2) PDF fallback only when HTML produced no usable chunks.
        if not chunks:
            pdf_path = resolve_pdf_path(aid)
            if pdf_path is None:
                failures.append(f"{aid}: no usable HTML or local PDF")
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
                "source": source,
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
    metadata = load_metadata()
    download_pdfs(metadata)       # fallback source
    download_html(metadata)       # skips cached, remembers 404s
    process_and_store(metadata)


if __name__ == "__main__":
    main()

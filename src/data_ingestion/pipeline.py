from pathlib import Path
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
    output_path: Path = cfg.PROCESSED_DIR / "chunks.parquet",
):
    df_meta = pd.DataFrame(metadata_list)

    # Recognize newer paper versions by base ID and keep latest updated
    df_meta["base_arxiv_id"] = df_meta["arxiv_id"].str.replace(r"v\d+$", "", regex=True)
    df_latest = (
        df_meta.sort_values("updated")
        .drop_duplicates("base_arxiv_id", keep="last")
        .reset_index(drop=True)
    )

    all_chunks = []
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

        # 2) PDF fallback: no HTML, or the conversion produced almost nothing
        if len(chunks) < 5:
            pdf_path = resolve_pdf_path(aid)
            if pdf_path is None:
                print(f"[Skip] No HTML or PDF for {aid}")
                continue
            try:
                pages = extract_pages(str(pdf_path))
                chunks = chunk_document(pages, aid, row["title"])
                source = "pdf"
            except Exception as e:
                print(f"[PDF failed] {aid}: {e}")
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

    if not all_chunks:
        print("No chunks produced. Check that HTML/PDFs exist in", cfg.DATA_DIR)
        return

    df_out = pd.DataFrame(all_chunks)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_parquet(output_path, index=False)
    print(f"Saved {len(df_out)} chunks from {df_out['arxiv_id'].nunique()} papers to {output_path}")
    print(df_out.groupby("source")["arxiv_id"].nunique())


def main():
    metadata = load_metadata()
    download_pdfs(metadata)       # fallback source
    download_html(metadata)       # skips cached, remembers 404s
    process_and_store(metadata)


if __name__ == "__main__":
    main()

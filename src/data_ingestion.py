import re
import time
from pathlib import Path
 
import pandas as pd
import pymupdf
import requests
from langchain_text_splitters import RecursiveCharacterTextSplitter
 
 
# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PDF_DIR = DATA_DIR / "pdfs"
META_DIR = DATA_DIR / "metadata"
PROCESSED_DIR = DATA_DIR / "processed"
 
FULL_METADATA_FILE = META_DIR / "arxiv_csAI_100_metadata.csv"
SAMPLE_FILE = META_DIR / "arxiv_csAI_25_pdf_sample.csv"
 
# arXiv asks automated clients to identify themselves
USER_AGENT = "btt-fallstudio-kpmg1f (leejooheon215@gmail.com)"
 
 
# Metadata loading
def load_metadata() -> list[dict]:
    """Load the 100-article metadata, filtered to a proof-of-concept sample."""
    df = pd.read_csv(FULL_METADATA_FILE)
    sample_ids = pd.read_csv(SAMPLE_FILE)["arxiv_id"]
    df = df[df["arxiv_id"].isin(sample_ids)]
    print(f"Using {len(df)} sample articles (from {FULL_METADATA_FILE.name})")
    return df.to_dict("records")
 
 
# PDF download
def resolve_pdf_path(arxiv_id: str) -> Path | None:
    """Find the local PDF for an arXiv ID."""
    matches = list(PDF_DIR.glob(f"{arxiv_id}_*.pdf")) + list(
        PDF_DIR.glob(f"{arxiv_id}.pdf")
    )
    return matches[0] if matches else None
 
 
def download_pdfs(metadata_list: list[dict], delay: float = 3.0) -> None:
    """Download each paper's pdf into data/pdfs/, skipping already downloaded pdfs"""
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": USER_AGENT}
 
    for row in metadata_list:
        arxiv_id = row["arxiv_id"]
        if resolve_pdf_path(arxiv_id):
            print(f"[Have] {arxiv_id}")
            continue
 
        try:
            resp = requests.get(row["pdf_url"], headers=headers, timeout=60)
            resp.raise_for_status()
            if not resp.content.startswith(b"%PDF"):
                raise ValueError("response is not a PDF")
            (PDF_DIR / f"{arxiv_id}.pdf").write_bytes(resp.content)
            print(f"[Downloaded] {arxiv_id}")
        except Exception as e:
            print(f"[Failed] {arxiv_id}: {e}")
 
        time.sleep(delay)  
 
 
# Task 4.2: PDF Extraction & Cleaning
def extract_and_clean_pdf(pdf_path: str) -> list[dict]:
    doc = pymupdf.open(pdf_path)
    pages_data = []
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text")
        # Remove headers, footers, page numbers, and whitespace
        text = re.sub(
            r"arXiv:\d{4}\.\d{4,5}(v\d+)?\s*\[.*?\]\s*\d{1,2}\s+\w+\s+\d{4}",
            "",
            text,
        )
        text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE).strip()
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()
        if text:
            pages_data.append({"page": page_num, "text": text})
    doc.close()
    return pages_data
 
 
# Task 4.3: Chunking Strategy & Outliers
def chunk_document(pages_data: list[dict], arxiv_id: str) -> list[dict]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks = []
    chunk_idx = 0
    for page in pages_data:
        for text_chunk in text_splitter.split_text(page["text"]):
            chunks.append(
                {
                    "chunk_id": f"{arxiv_id}_c{chunk_idx:04d}",
                    "arxiv_id": arxiv_id,
                    "page_number": page["page"],
                    "text": text_chunk,
                }
            )
            chunk_idx += 1
 
    if len(chunks) > 200:
        print(f"[Warning] Large document detected: {arxiv_id} ({len(chunks)} chunks)")
 
    return chunks
 
 
# Task 4.4: Deduplication & Storage
def process_and_store(
    metadata_list: list[dict],
    output_path: Path = PROCESSED_DIR / "chunks.parquet",
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
        pdf_path = resolve_pdf_path(row["arxiv_id"])
        if pdf_path is None:
            print(f"[Skip] No local PDF for {row['arxiv_id']}")
            continue
 
        print(f"[Found] {pdf_path.name}")
        pages = extract_and_clean_pdf(str(pdf_path))
        for c in chunk_document(pages, row["arxiv_id"]):
            c.update(
                {
                    "title": row["title"],
                    "categories": row["categories"],
                    "authors": row["authors"],
                    "abstract": row["abstract"],
                    "published": row["published"],
                    "updated": row["updated"],
                    "pdf_url": row["pdf_url"],
                }
            )
            all_chunks.append(c)
 
    if not all_chunks:
        print("No chunks produced. Check that PDFs exist in", PDF_DIR)
        return
 
    df_out = pd.DataFrame(all_chunks)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_parquet(output_path, index=False)
    print(
        f"Saved {len(df_out)} chunks from {df_out['arxiv_id'].nunique()} papers to {output_path}"
    )
 
 
# Task 4.1: Pipeline Entry Point
if __name__ == "__main__":
    metadata = load_metadata()   # 25-paper sample with full metadata
    download_pdfs(metadata)      # metadata -> PDFs (skips ones already downloaded)
    process_and_store(metadata)  # PDFs -> text -> chunks -> parquet
 
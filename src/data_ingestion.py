# ingestion.py
import re
import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pandas as pd

# Task 4.2: PDF Extraction & Cleaning
def extract_and_clean_pdf(pdf_path: str) -> list[dict]:
    doc = fitz.open(pdf_path)
    pages_data = []
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text")
        # Remove headers/footers/page numbers
        text = re.sub(
            r"arXiv:\d{4}\.\d{4,5}(v\d+)?\s*\[.*?\]\s*\d{1,2}\s+\w+\s+\d{4}",
            "",
            text,
        )
        text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE).strip()
        if text:
            pages_data.append({"page": page_num, "text": text})
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
def process_and_store(metadata_list: list[dict], output_path: str = "chunks.parquet"):
    df_meta = pd.DataFrame(metadata_list)

    # Recognize newer paper versions by base ID and keep latest updated
    df_meta["base_arxiv_id"] = df_meta["arxiv_id"].str.split("v").str[0]
    df_latest = (
        df_meta.sort_values("updated").groupby("base_arxiv_id").last().reset_index()
    )

    all_chunks = []
    for _, row in df_latest.iterrows():
        pages = extract_and_clean_pdf(row["pdf_url"])
        chunks = chunk_document(pages, row["arxiv_id"])
        for c in chunks:
            c.update({"title": row["title"], "categories": row["categories"]})
            all_chunks.append(c)

    df_out = pd.DataFrame(all_chunks)
    df_out.to_parquet(output_path, index=False)
    print(f"Successfully saved {len(df_out)} chunks to {output_path}")


# ==========================================
# Task 4.1: Architecture Pipeline Entry Point
# ==========================================
if __name__ == "__main__":
    # Test sample data or load real metadata list
    sample_metadata = [...]  # Your metadata records from EDA
    process_and_store(sample_metadata)
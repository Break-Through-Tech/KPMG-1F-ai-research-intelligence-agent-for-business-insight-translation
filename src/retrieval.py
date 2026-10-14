import argparse
import json

import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHUNKS_FILE = PROJECT_ROOT / "data" / "processed" / "chunks.parquet"
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma_db"
COLLECTION_NAME = "arxiv_papers"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
REQUIRED_COLUMNS = {"chunk_id", "text", "arxiv_id", "title"}
def load_chunks():
    if not CHUNKS_FILE.exists():
        raise FileNotFoundError(
            f"Chunks file not found: {CHUNKS_FILE}"
        )

    df = pd.read_parquet(CHUNKS_FILE)

    print(f"Loaded {len(df)} chunks")
    print(f"From {df['arxiv_id'].nunique()} papers")

    return df

def create_embeddings(df):
    model = SentenceTransformer(EMBEDDING_MODEL)

    texts = df["text"].tolist()

    embeddings = model.encode(
        texts,
        show_progress_bar=True
    )

    print(f"Created {len(embeddings)} embeddings")
    print(f"Embedding size: {embeddings.shape[1]}")

    return embeddings

def citation_metadata(row):
    """Keep source fields in Chroma so results can be cited."""
    metadata = {
        "arxiv_id": str(row["arxiv_id"]),
        "title": str(row["title"]),
    }

    for field in [
        "page_number",
        "pdf_url",
        "html_url",
        "section",
        "subsection",
        "source",
    ]:
        if field in row.index and pd.notna(row[field]):
            value = row[field]
            if field == "page_number":
                metadata[field] = int(value)
            else:
                metadata[field] = str(value)

    return metadata


def store_embeddings(df, embeddings):
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Chunk data missing columns: {', '.join(sorted(missing))}")
    if df.empty or df[list(REQUIRED_COLUMNS)].isna().any().any():
        raise ValueError("Chunk data is empty or contains missing required fields")
    if df["text"].astype(str).str.strip().eq("").any():
        raise ValueError("Chunk data contains empty text")
    ids = df["chunk_id"].astype(str).tolist()
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate chunk IDs in input")
    if len(embeddings) != len(df):
        raise ValueError("Embedding count does not match chunk count")

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME
    )
    indexed_model = (collection.metadata or {}).get("embedding_model")
    if indexed_model and indexed_model != EMBEDDING_MODEL:
        raise ValueError(
            f"Index uses {indexed_model}, expected {EMBEDDING_MODEL}; rebuild the collection"
        )

    # Upsert refreshes existing rows (including indexes created before metadata
    # was stored). Delete IDs absent from this corpus so reruns do not serve stale papers.
    existing_ids = set(collection.get(include=[])["ids"])
    stale_ids = sorted(existing_ids - set(ids))

    collection.upsert(
        ids=ids,
        documents=df["text"].tolist(),
        embeddings=embeddings.tolist(),
        metadatas=[citation_metadata(row) for _, row in df.iterrows()],
    )
    if stale_ids:
        collection.delete(ids=stale_ids)
    collection.modify(metadata={"embedding_model": EMBEDDING_MODEL})

    print(f"Stored {collection.count()} chunks in ChromaDB ({len(stale_ids)} stale removed)")

    return collection


def search(query, top_k=5, *, client=None, model=None):
    """Return ranked passages with their paper and page citation fields."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query must be non-empty text")
    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
        raise ValueError("top_k must be a positive integer")

    client = client or chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(name=COLLECTION_NAME)
    if (collection.metadata or {}).get("embedding_model") != EMBEDDING_MODEL:
        raise ValueError("Index model is unknown or different; rerun indexing first")
    count = collection.count()
    if count == 0:
        return []

    model = model or SentenceTransformer(EMBEDDING_MODEL)
    query_vector = model.encode([query.strip()]).tolist()
    result = collection.query(
        query_embeddings=query_vector,
        n_results=min(top_k, count),
        include=["documents", "metadatas", "distances"],
    )
    hits = []
    for chunk_id, passage, metadata, distance in zip(
        result["ids"][0],
        result["documents"][0],
        result["metadatas"][0],
        result["distances"][0],
    ):
        if not metadata or not all(key in metadata for key in ("arxiv_id", "title")):
            raise ValueError("Index contains passages without citations; rerun indexing first")
        hits.append({
            "chunk_id": chunk_id,
            "text": passage,
            "distance": distance,
            "arxiv_id": metadata["arxiv_id"],
            "title": metadata["title"],
            "page_number": metadata.get("page_number"),
            "pdf_url": metadata.get("pdf_url"),
            "html_url": metadata.get("html_url"),
            "section": metadata.get("section"),
            "subsection": metadata.get("subsection"),
            "source": metadata.get("source"),
        })
    return hits

def search_chunks(query, top_k=5):
    """Compatibility wrapper used by agent.py."""
    return search(query, top_k=top_k)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build or query the local arXiv vector index")
    parser.add_argument("--query", help="Search indexed chunks instead of rebuilding the index")
    parser.add_argument("--top-k", type=int, default=5, help="Maximum search results (default: 5)")
    args = parser.parse_args()
    if args.query is not None:
        print(json.dumps(search(args.query, args.top_k), indent=2))
    else:
        chunks = load_chunks()
        embeddings = create_embeddings(chunks)
        store_embeddings(chunks, embeddings)

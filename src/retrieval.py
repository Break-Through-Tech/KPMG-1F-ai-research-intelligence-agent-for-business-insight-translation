import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHUNKS_FILE = PROJECT_ROOT / "data" / "processed" / "chunks.parquet"
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma_db"
COLLECTION_NAME = "arxiv_papers"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
REQUIRED_COLUMNS = {"chunk_id", "text", "arxiv_id", "title", "page_number", "pdf_url"}

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
    """Keep source fields in Chroma so results can be cited without Parquet."""
    return {
        "arxiv_id": str(row["arxiv_id"]),
        "title": str(row["title"]),
        "page_number": int(row["page_number"]),
        "pdf_url": str(row["pdf_url"]),
    }


def store_embeddings(df, embeddings):
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Chunk data missing columns: {', '.join(sorted(missing))}")
    if df.empty or df[list(REQUIRED_COLUMNS)].isna().any().any():
        raise ValueError("Chunk data is empty or contains missing source fields")
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

if __name__ == "__main__":
    chunks = load_chunks()
    embeddings = create_embeddings(chunks)
    collection = store_embeddings(chunks, embeddings)

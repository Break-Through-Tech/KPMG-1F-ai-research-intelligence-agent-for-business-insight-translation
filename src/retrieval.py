import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHUNKS_FILE = PROJECT_ROOT / "data" / "processed" / "chunks.parquet"
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma_db"

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
    model = SentenceTransformer("all-MiniLM-L6-v2")

    texts = df["text"].tolist()

    embeddings = model.encode(
        texts,
        show_progress_bar=True
    )

    print(f"Created {len(embeddings)} embeddings")
    print(f"Embedding size: {embeddings.shape[1]}")

    return embeddings

def store_embeddings(df, embeddings):
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    collection = client.get_or_create_collection(
        name="arxiv_papers"
    )

    collection.upsert(
        ids=df["chunk_id"].tolist(),
        documents=df["text"].tolist(),
        embeddings=embeddings.tolist()
    )

    print(f"Stored {collection.count()} chunks in ChromaDB")

    return collection

if __name__ == "__main__":
    chunks = load_chunks()
    embeddings = create_embeddings(chunks)
    collection = store_embeddings(chunks, embeddings)
import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHUNKS_FILE = PROJECT_ROOT / "data" / "processed" / "chunks.parquet"
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma_db"
COLLECTION_NAME = "arxiv_papers"


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

def get_collection():
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    try:
        return client.get_collection(name=COLLECTION_NAME)
    except Exception as e:
        raise RuntimeError(
            "ChromaDB collection not found. Run src/retrieval.py first."
        ) from e
    
def store_embeddings(df, embeddings):
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    existing_collections = client.list_collections()

    existing_names = [
        collection.name if hasattr(collection, "name") else str(collection)
        for collection in existing_collections
    ]

    if COLLECTION_NAME in existing_names:
        client.delete_collection(name=COLLECTION_NAME)
        print("Deleted old ChromaDB collection")

    collection = client.create_collection(
        name=COLLECTION_NAME
    )

    metadatas = []

    for _, row in df.iterrows():
        metadata = {
            "arxiv_id": str(row["arxiv_id"]),
            "page_number": int(row["page_number"]),
            "title": str(row["title"]),
            "categories": str(row["categories"]),
            "authors": str(row["authors"]),
            "pdf_url": str(row["pdf_url"]),
        }

        metadatas.append(metadata)

    collection.add(
        ids=df["chunk_id"].tolist(),
        documents=df["text"].tolist(),
        embeddings=embeddings.tolist(),
        metadatas=metadatas
    )

    print(f"Stored {collection.count()} chunks in ChromaDB")

    return collection

if __name__ == "__main__":
    chunks = load_chunks()
    embeddings = create_embeddings(chunks)
    collection = store_embeddings(chunks, embeddings)
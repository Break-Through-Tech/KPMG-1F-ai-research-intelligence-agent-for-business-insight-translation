
import argparse
import base64
import json
from urllib.parse import urlsplit, urlunsplit

import numpy as np
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SearchableField,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)


# --------------------------------------------------
# Configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHUNKS_FILE = PROJECT_ROOT / "data" / "processed" / "chunks.parquet"

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384
BATCH_SIZE = 100

load_dotenv(PROJECT_ROOT / ".env")

AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_ADMIN_KEY = os.getenv("AZURE_SEARCH_ADMIN_KEY")
AZURE_SEARCH_QUERY_KEY = os.getenv("AZURE_SEARCH_QUERY_KEY")
INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME", "arxiv-papers")


# --------------------------------------------------
# Load data and create embeddings
# --------------------------------------------------

def load_chunks():
    if not CHUNKS_FILE.exists():
        raise FileNotFoundError(f"Missing chunks file: {CHUNKS_FILE}")

    df = pd.read_parquet(CHUNKS_FILE)

    required = {"chunk_id", "arxiv_id", "title", "text", "pdf_url"}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    if df.empty:
        raise ValueError("The chunks dataset is empty")

    if df["chunk_id"].isna().any() or df["chunk_id"].duplicated().any():
        raise ValueError("Chunk IDs must be present and unique")

    print(f"Loaded {len(df)} chunks")
    print(f"From {df['arxiv_id'].nunique()} papers")

    return df


def create_embeddings(df):
    validate_chunks(df)
    model = SentenceTransformer(MODEL_NAME)

    embeddings = model.encode(
        df["text"].astype(str).tolist(),
        show_progress_bar=True,
    )

    if embeddings.shape[1] != EMBEDDING_DIMENSIONS:
        raise ValueError("Embedding dimension mismatch")

    print(f"Created {len(embeddings)} embeddings")
    print(f"Embedding size: {embeddings.shape[1]}")

    return validate_embeddings(embeddings, len(df))


def make_azure_key(chunk_id):
    return base64.urlsafe_b64encode(
        str(chunk_id).encode("utf-8")
    ).decode("utf-8")


def safe_text(row, field, default=""):
    value = row.get(field)
    if isinstance(value, (list, tuple, np.ndarray)):
        return ", ".join(str(item) for item in value if item is not None)
    if value is None or pd.isna(value):
        return default
    return str(value).strip()


# --------------------------------------------------
# Citation metadata
# --------------------------------------------------

def validate_url(value, field):
    parts = urlsplit(value)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise ValueError(f"{field} must be an HTTP(S) source URL")


def validate_chunks(df):
    required = {"chunk_id", "arxiv_id", "title", "text", "pdf_url"}
    if required - set(df.columns):
        raise ValueError(f"Missing columns: {sorted(required - set(df.columns))}")
    if df.empty:
        raise ValueError("The chunks dataset is empty")
    for field in ("chunk_id", "arxiv_id", "title", "text"):
        if not df[field].map(lambda v: isinstance(v, str) and bool(v.strip())).all():
            raise ValueError(f"{field} must contain non-empty text")
    if df["chunk_id"].duplicated().any():
        raise ValueError("Chunk IDs must be present and unique")
    for _, row in df.iterrows():
        citation_metadata(row)


def validate_embeddings(embeddings, count):
    vectors = np.asarray(embeddings, dtype=float)
    if vectors.shape != (count, EMBEDDING_DIMENSIONS) or not np.isfinite(vectors).all():
        raise ValueError("Expected finite 384-dimensional embeddings, one per chunk")
    return vectors


def citation_metadata(row):
    source = safe_text(row, "source", "pdf")

    if source not in ("html", "pdf"):
        raise ValueError(f"Unknown source: {source}")

    pdf_url = safe_text(row, "pdf_url")
    html_url = safe_text(row, "html_url")
    page_number = None

    if source == "html":
        if not html_url:
            raise ValueError("HTML chunk is missing html_url")
        validate_url(html_url, "html_url")
        source_url = html_url

    else:
        if not pdf_url:
            raise ValueError("PDF chunk is missing pdf_url")

        page = row.get("page_number")
        if page is None or pd.isna(page) or isinstance(page, bool):
            raise ValueError("PDF chunk must have a valid page number")

        try:
            page_number = int(page)
            valid = page_number > 0 and float(page) == page_number
        except (TypeError, ValueError, OverflowError):
            valid = False

        if not valid:
            raise ValueError("Invalid PDF page number")

        validate_url(pdf_url, "pdf_url")
        parts = urlsplit(pdf_url)
        source_url = urlunsplit(parts._replace(fragment=f"page={page_number}"))

    flag = row.get("high_value", False)
    if flag is None or pd.isna(flag):
        high_value = False
    elif isinstance(flag, (bool, np.bool_)):
        high_value = bool(flag)
    else:
        raise ValueError("high_value must be a boolean")

    return {
        "source": source,
        "page_number": page_number,
        "html_url": html_url,
        "pdf_url": pdf_url,
        "source_url": source_url,
        "section": safe_text(row, "section"),
        "subsection": safe_text(row, "subsection"),
        "high_value": high_value,
    }


# --------------------------------------------------
# Azure clients
# --------------------------------------------------

def check_admin_config():
    if not AZURE_SEARCH_ENDPOINT or not AZURE_SEARCH_ADMIN_KEY:
        raise RuntimeError(
            "AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_ADMIN_KEY are required"
        )


def get_index_client():
    check_admin_config()

    return SearchIndexClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        credential=AzureKeyCredential(AZURE_SEARCH_ADMIN_KEY),
    )


def get_search_client():
    check_admin_config()

    return SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(AZURE_SEARCH_ADMIN_KEY),
    )


def get_query_search_client():
    key = AZURE_SEARCH_QUERY_KEY or AZURE_SEARCH_ADMIN_KEY

    if not AZURE_SEARCH_ENDPOINT or not key:
        raise RuntimeError(
            "Azure endpoint and a query or admin key are required"
        )

    return SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(key),
    )


# --------------------------------------------------
# Create Azure vector index
# --------------------------------------------------

def create_index(*, rebuild=False):
    if not rebuild:
        raise ValueError("Index replacement requires explicit rebuild=True")
    client = get_index_client()

    fields = [
        SimpleField(
            name="chunk_id",
            type=SearchFieldDataType.String,
            key=True,
            filterable=True,
        ),
        SearchableField(
            name="text",
            type=SearchFieldDataType.String,
        ),
        SearchField(
            name="embedding",
            type=SearchFieldDataType.Collection(
                SearchFieldDataType.Single
            ),
            searchable=True,
            vector_search_dimensions=EMBEDDING_DIMENSIONS,
            vector_search_profile_name="vector-profile",
        ),
        SimpleField(
            name="arxiv_id",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SimpleField(
            name="page_number",
            type=SearchFieldDataType.Int32,
            filterable=True,
        ),
        SearchableField(
            name="title",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SearchableField(
            name="authors",
            type=SearchFieldDataType.String,
        ),
        SearchableField(
            name="categories",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SimpleField(
            name="pdf_url",
            type=SearchFieldDataType.String,
        ),

        # New HTML/citation fields
        SimpleField(
            name="source",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SimpleField(
            name="html_url",
            type=SearchFieldDataType.String,
        ),
        SimpleField(
            name="source_url",
            type=SearchFieldDataType.String,
        ),
        SearchableField(
            name="section",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SearchableField(
            name="subsection",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SimpleField(
            name="high_value",
            type=SearchFieldDataType.Boolean,
            filterable=True,
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(name="hnsw-config")
        ],
        profiles=[
            VectorSearchProfile(
                name="vector-profile",
                algorithm_configuration_name="hnsw-config",
            )
        ],
    )

    if INDEX_NAME in list(client.list_index_names()):
        client.delete_index(INDEX_NAME)
        print(f"Deleted previous index: {INDEX_NAME}")

    index = SearchIndex(
        name=INDEX_NAME,
        fields=fields,
        vector_search=vector_search,
    )

    client.create_index(index)

    print(f"Created Azure index: {INDEX_NAME}")


# --------------------------------------------------
# Upload embeddings and metadata
# --------------------------------------------------

def store_embeddings(df, embeddings):
    """Upload supplied chunks; does not remove stale IDs. Use explicit rebuild for corpus replacement."""
    validate_chunks(df)
    embeddings = validate_embeddings(embeddings, len(df))
    if len(df) != len(embeddings):
        raise ValueError("Chunks and embeddings count mismatch")

    if df["chunk_id"].isna().any() or df["chunk_id"].duplicated().any():
        raise ValueError("Chunk IDs must be present and unique")

    documents = []

    for (_, row), embedding in zip(df.iterrows(), embeddings):
        citation = citation_metadata(row)

        document = {
            "chunk_id": make_azure_key(row["chunk_id"]),
            "text": str(row["text"]),
            "embedding": embedding.tolist(),
            "arxiv_id": safe_text(row, "arxiv_id"),
            "title": safe_text(row, "title"),
            "authors": safe_text(row, "authors"),
            "categories": safe_text(row, "categories"),
            **citation,
        }

        documents.append(document)

    client = get_search_client()
    successful = 0

    for start in range(0, len(documents), BATCH_SIZE):
        batch = documents[start:start + BATCH_SIZE]
        results = client.upload_documents(documents=batch)

        successful += sum(result.succeeded for result in results)

        for result in results:
            if not result.succeeded:
                print("Upload error:", result.error_message)

        print(f"Uploaded {min(start + BATCH_SIZE, len(documents))}/{len(documents)}")

    print(f"Successfully uploaded: {successful}/{len(documents)}")

    if successful != len(documents):
        raise RuntimeError("Some chunks failed to upload")

    print(f"Documents currently reported by Azure: {client.get_document_count()}")


# --------------------------------------------------
# Search for relevant research chunks
# --------------------------------------------------

def search_chunks(query, top_k=5, hybrid=False, *, client=None, model=None):
    """Query Azure with MiniLM vectors and return validated HTML/PDF citations."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query must be non-empty text")

    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
        raise ValueError("top_k must be a positive integer")

    model = model if model is not None else SentenceTransformer(MODEL_NAME)
    query_embedding = model.encode(query.strip()).tolist()

    validate_embeddings([query_embedding], 1)
    client = client if client is not None else get_query_search_client()

    vector_query = VectorizedQuery(
        vector=query_embedding,
        k_nearest_neighbors=top_k,
        fields="embedding",
    )

    results = client.search(
        search_text=query.strip() if hybrid else None,
        vector_queries=[vector_query],
        select=[
            "chunk_id",
            "text",
            "title",
            "arxiv_id",
            "page_number",
            "authors",
            "categories",
            "pdf_url",
            "html_url",
            "source_url",
            "source",
            "section",
            "subsection",
            "high_value",
        ],
        top=top_k,
    )

    retrieved = []

    for result in results:
        citation = citation_metadata(result)
        for field in ("text", "title", "arxiv_id"):
            if not safe_text(result, field):
                raise ValueError(f"Azure result missing {field}")
        retrieved.append({
            "chunk_id": result.get("chunk_id"),
            "text": result.get("text"),
            "title": result.get("title"),
            "arxiv_id": result.get("arxiv_id"),
            "page_number": result.get("page_number"),
            "authors": result.get("authors"),
            "categories": result.get("categories"),
            "pdf_url": result.get("pdf_url"),
            "html_url": result.get("html_url"),
            "source_url": result.get("source_url"),
            "source": result.get("source"),
            "section": result.get("section"),
            "subsection": result.get("subsection"),
            "high_value": result.get("high_value"),
            "score": result["@search.score"],
            **citation,
        })

    return retrieved


def search(query, top_k=5, *, hybrid=False, client=None, model=None):
    """Public retrieval entry point; uses the same Azure backend as search_chunks."""
    return search_chunks(query, top_k, hybrid, client=client, model=model)


def main():
    parser = argparse.ArgumentParser(description="Query Azure or explicitly rebuild its index")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--query", help="Retrieve passages without modifying the index")
    mode.add_argument("--rebuild", action="store_true", help="Destructively replace the shared index")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--hybrid", action="store_true")
    args = parser.parse_args()
    if args.query is not None:
        print(json.dumps(search(args.query, args.top_k, hybrid=args.hybrid), indent=2))
        return
    chunks = load_chunks()
    validate_chunks(chunks)
    embeddings = create_embeddings(chunks)
    create_index(rebuild=True)
    store_embeddings(chunks, embeddings)


if __name__ == "__main__":
    main()

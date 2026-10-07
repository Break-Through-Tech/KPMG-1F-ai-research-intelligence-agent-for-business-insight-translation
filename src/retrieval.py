import base64
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
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

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHUNKS_FILE = PROJECT_ROOT / "data" / "processed" / "chunks.parquet"

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384
BATCH_SIZE = 100

load_dotenv()

AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_ADMIN_KEY = os.getenv("AZURE_SEARCH_ADMIN_KEY")
INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME", "arxiv-papers")


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
    model = SentenceTransformer(MODEL_NAME)

    texts = df["text"].astype(str).tolist()

    embeddings = model.encode(
        texts,
        show_progress_bar=True,
    )

    print(f"Created {len(embeddings)} embeddings")
    print(f"Embedding size: {embeddings.shape[1]}")

    if embeddings.shape[1] != EMBEDDING_DIMENSIONS:
        raise ValueError(
            f"Embedding dimension does not match expected size of "
            f"{EMBEDDING_DIMENSIONS}"
        )

    return embeddings


def make_azure_key(chunk_id):
    return base64.urlsafe_b64encode(
        str(chunk_id).encode("utf-8")
    ).decode("utf-8")


def check_azure_config():
    if not AZURE_SEARCH_ENDPOINT:
        raise RuntimeError(
            "AZURE_SEARCH_ENDPOINT is missing from .env"
        )

    if not AZURE_SEARCH_ADMIN_KEY:
        raise RuntimeError(
            "AZURE_SEARCH_ADMIN_KEY is missing from .env"
        )


def get_index_client():
    check_azure_config()

    return SearchIndexClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        credential=AzureKeyCredential(
            AZURE_SEARCH_ADMIN_KEY
        ),
    )


def get_search_client():
    check_azure_config()

    return SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=INDEX_NAME,
        credential=AzureKeyCredential(
            AZURE_SEARCH_ADMIN_KEY
        ),
    )


def create_index():
    index_client = get_index_client()

    existing_indexes = list(
        index_client.list_index_names()
    )

    if INDEX_NAME in existing_indexes:
        index_client.delete_index(INDEX_NAME)
        print(
            f"Deleted old Azure index: {INDEX_NAME}"
        )

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
    ]

    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="hnsw-config"
            )
        ],
        profiles=[
            VectorSearchProfile(
                name="vector-profile",
                algorithm_configuration_name="hnsw-config",
            )
        ],
    )

    index = SearchIndex(
        name=INDEX_NAME,
        fields=fields,
        vector_search=vector_search,
    )

    index_client.create_index(index)

    print(
        f"Created fresh Azure AI Search index: {INDEX_NAME}"
    )


def store_embeddings(df, embeddings):
    if len(df) != len(embeddings):
        raise ValueError(
            "Number of chunks does not match number of embeddings"
        )

    client = get_search_client()

    documents = []

    for (_, row), embedding in zip(
        df.iterrows(),
        embeddings,
    ):
        document = {
            "chunk_id": make_azure_key(
                row["chunk_id"]
            ),
            "text": str(
                row["text"]
            ),
            "embedding": embedding.tolist(),
            "arxiv_id": str(
                row["arxiv_id"]
            ),
            "page_number": int(
                row["page_number"]
            ),
            "title": str(
                row["title"]
            ),
            "authors": str(
                row["authors"]
            ),
            "categories": str(
                row["categories"]
            ),
            "pdf_url": str(
                row["pdf_url"]
            ),
        }

        documents.append(document)

    successful = 0

    for start in range(
        0,
        len(documents),
        BATCH_SIZE,
    ):
        batch = documents[
            start:start + BATCH_SIZE
        ]

        results = client.upload_documents(
            documents=batch
        )

        batch_success = sum(
            result.succeeded
            for result in results
        )

        successful += batch_success

        print(
            f"Uploaded "
            f"{min(start + BATCH_SIZE, len(documents))}"
            f"/{len(documents)}"
        )

        for result in results:
            if not result.succeeded:
                print(
                    "Upload error:",
                    result.error_message,
                )

    print()

    print(
        f"Successfully uploaded: "
        f"{successful}/{len(documents)}"
    )

    print(
        f"Documents in Azure: "
        f"{client.get_document_count()}"
    )


if __name__ == "__main__":
    chunks = load_chunks()
    embeddings = create_embeddings(chunks)

    create_index()
    store_embeddings(chunks, embeddings)
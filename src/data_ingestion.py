"""Compatibility entrypoint: python src/data_ingestion.py."""

from data_ingestion.pdf_pipeline import run_pipeline


if __name__ == "__main__":
    run_pipeline()

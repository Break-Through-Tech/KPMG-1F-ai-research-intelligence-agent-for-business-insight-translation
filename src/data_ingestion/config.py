from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PDF_DIR = DATA_DIR / "pdfs"
HTML_DIR = DATA_DIR / "html"
META_DIR = DATA_DIR / "metadata"
PROCESSED_DIR = DATA_DIR / "processed"

FULL_METADATA_FILE = META_DIR / "arxiv_csAI_100_metadata.csv"
SAMPLE_FILE = META_DIR / "arxiv_csAI_25_pdf_sample.csv"

# arXiv asks automated clients to identify themselves
USER_AGENT = "btt-fallstudio-kpmg1f (leejooheon215@gmail.com)"

import time
from pathlib import Path
import requests
from . import config as cfg

# PDF download
def resolve_pdf_path(arxiv_id: str) -> Path | None:
    """Find the local PDF for an arXiv ID."""
    matches = list(cfg.PDF_DIR.glob(f"{arxiv_id}_*.pdf")) + list(
        cfg.PDF_DIR.glob(f"{arxiv_id}.pdf")
    )
    return matches[0] if matches else None


def download_pdfs(metadata_list: list[dict], delay: float = 3.0) -> None:
    """Download each paper's pdf into data/pdfs/, skipping already downloaded pdfs"""
    cfg.PDF_DIR.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": cfg.USER_AGENT}

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
            (cfg.PDF_DIR / f"{arxiv_id}.pdf").write_bytes(resp.content)
            print(f"[Downloaded] {arxiv_id}")
        except Exception as e:
            print(f"[Failed] {arxiv_id}: {e}")

        time.sleep(delay)
# HTML download + parsing
def download_html(metadata_list: list[dict], delay: float = 3.0) -> None:
    """Cache arXiv's HTML version of each paper in data/html/. Papers with no HTML get a .nohtml marker."""
    cfg.HTML_DIR.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": cfg.USER_AGENT}

    for row in metadata_list:
        aid = row["arxiv_id"]
        path, miss = cfg.HTML_DIR / f"{aid}.html", cfg.HTML_DIR / f"{aid}.nohtml"
        if path.exists() or miss.exists():
            print(f"[Have] html {aid}")
            continue
        try:
            resp = requests.get(f"https://arxiv.org/html/{aid}", headers=headers, timeout=60)
            if resp.status_code == 200:
                path.write_text(resp.text, encoding="utf-8")
                print(f"[Downloaded] html {aid}")
            elif resp.status_code == 404:
                miss.touch()
                print(f"[No HTML] {aid}")
            elif resp.status_code == 429:
                print("[Throttled] HTTP 429, stopping. Wait 10-15 min and rerun.")
                break
            else:
                print(f"[Failed] {aid}: HTTP {resp.status_code}")
        except Exception as e:
            print(f"[Failed] {aid}: {e}")
        time.sleep(delay)


def load_html(arxiv_id: str) -> str | None:
    path = cfg.HTML_DIR / f"{arxiv_id}.html"
    return path.read_text(encoding="utf-8") if path.exists() else None

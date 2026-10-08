import pandas as pd
from . import config as cfg

# Metadata loading
def load_metadata() -> list[dict]:
    """Load the 100-article metadata, filtered to a proof-of-concept sample."""
    df = pd.read_csv(cfg.FULL_METADATA_FILE)
    sample_ids = pd.read_csv(cfg.SAMPLE_FILE)["arxiv_id"].dropna().astype(str)
    missing = sorted(set(sample_ids) - set(df["arxiv_id"].astype(str)))
    if missing:
        raise ValueError(
            f"Sample IDs absent from {cfg.FULL_METADATA_FILE.name}: {', '.join(missing)}. "
            "Use a matching metadata snapshot before ingestion."
        )
    df = df[df["arxiv_id"].isin(sample_ids)]
    print(f"Using {len(df)} sample articles (from {cfg.FULL_METADATA_FILE.name})")
    return df.to_dict("records")

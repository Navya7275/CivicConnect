"""Web scraping and data fetcher module for India Code and MyScheme.

Features:
- Local caching of raw HTML/JSON downloads
- HTTP timeout handling and clean error logging
- MyScheme fallback dataset loading via Hugging Face shrijayan/gov_myscheme or direct API/dataset
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

RAW_DATA_DIR = Path(__file__).parent / "raw_data"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingestion_scrape")


def fetch_url(url: str, timeout: int = 15) -> Optional[str]:
    """Fetch content from HTTP URL with timeout and error logging."""
    try:
        headers = {
            "User-Agent": "CivicConnect-AcademicPipeline/1.0 (Indian Legal & Welfare Research)"
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Failed to fetch URL {url}: {e}")
        return None


def fetch_myscheme_pilot_data() -> List[Dict[str, Any]]:
    """Fetch or load pilot welfare schemes from seed_schemes.json.
    
    Note: Unverified third-party mirrors (such as Hugging Face shrijayan/gov_myscheme)
    are intentionally avoided in favor of hand-curated, ministry-verified seed records.
    Full automated scraping directly from official portals is tracked under Issue #5.
    """
    cache_path = RAW_DATA_DIR / "myscheme_pilot.json"
    seed_schemes_path = Path(__file__).parent / "seed_schemes.json"

    if cache_path.exists():
        logger.info(f"Loading MyScheme pilot data from local cache: {cache_path}")
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)

    if seed_schemes_path.exists():
        logger.info(f"Loading hand-curated pilot welfare schemes from {seed_schemes_path}...")
        with open(seed_schemes_path, "r", encoding="utf-8") as f:
            schemes = json.load(f)
    else:
        logger.warning(f"Seed schemes file not found at {seed_schemes_path}")
        schemes = []

    # Optional: third-party Hugging Face dataset attempt disabled to guarantee authoritative provenance.
    # hf_url = "https://datasets-server.huggingface.co/rows?dataset=shrijayan/gov_myscheme&config=default&split=train&offset=0&length=50"

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(schemes, f, indent=2)

    logger.info(f"Saved {len(schemes)} raw welfare schemes to cache: {cache_path}")
    return schemes


if __name__ == "__main__":
    schemes = fetch_myscheme_pilot_data()
    print(f"Scraped/Loaded {len(schemes)} welfare scheme records.")

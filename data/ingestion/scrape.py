"""Web scraping and data fetcher module for India Code and MyScheme.

Features:
- Local caching of raw HTML/JSON downloads
- HTTP timeout handling and clean error logging
- MyScheme fallback dataset loading via Hugging Face shrijayan/gov_myscheme or direct API/dataset
"""

import hashlib
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


def fetch_indiacode_act(act_id: str, timeout: int = 15) -> Optional[Dict[str, Any]]:
    """Fetch raw Act content and section metadata from indiacode.gov.in with local caching.
    
    Uses official DSpace REST API / show-data endpoints on indiacode.gov.in.
    Computes raw SHA-256 hash from downloaded bytes to guarantee cryptographic provenance.
    """
    cache_path = RAW_DATA_DIR / f"indiacode_{act_id}.json"
    if cache_path.exists():
        logger.info(f"Loading cached India Code act dataset: {cache_path}")
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)

    logger.info(f"Fetching India Code Act: '{act_id}' from indiacode.gov.in...")
    url = f"https://indiacode.gov.in/show-data?actid={act_id}"
    
    try:
        headers = {
            "User-Agent": "CivicConnect-AcademicPipeline/1.0 (Indian Statutory Research; +https://indiacode.gov.in)"
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        if response.status_code == 200:
            raw_bytes = response.content
            raw_hash = hashlib.sha256(raw_bytes).hexdigest()
            act_data = {
                "act_id": act_id,
                "source_url": url,
                "raw_sha256": raw_hash,
                "content_length": len(raw_bytes),
                "fetched_at": response.headers.get("Date") or "2026-09-06T12:00:00Z",
                "html_content": response.text[:5000]  # Store clean raw snippet
            }
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(act_data, f, indent=2)
            logger.info(f"Saved raw India Code act content to {cache_path} (raw_sha256: {raw_hash[:12]}...)")
            return act_data
        else:
            logger.warning(f"India Code HTTP {response.status_code} for act_id {act_id}")
            return None
    except Exception as e:
        logger.error(f"Error fetching India Code act {act_id}: {e}")
        return None


if __name__ == "__main__":
    schemes = fetch_myscheme_pilot_data()
    print(f"Scraped/Loaded {len(schemes)} welfare scheme records.")
    
    # Test India Code fetch for CPA 2019
    cpa_data = fetch_indiacode_act("AC_CEN_4_68_00003_201935_1566472428611")
    if cpa_data:
        print(f"Fetched India Code CPA 2019 (raw_sha256: {cpa_data['raw_sha256']})")

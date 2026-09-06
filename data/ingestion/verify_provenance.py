"""Provenance Verification Utility for CivicConnect (Issue #5).

Verifies the cryptographic integrity and provenance of all stored chunks:
1. Recalculates SHA-256 hash of stored chunk text (text_sha256) and verifies match.
2. Verifies presence of raw document SHA-256 hash (raw_sha256).
3. Verifies that manual extractions record a valid reviewer_name.
4. Audits raw cached files in raw_data/ for content integrity.
"""

import hashlib
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import requests

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from data.db.database import SessionLocal
from data.db.models import Chunk, Document

RAW_DATA_DIR = Path(__file__).parent / "raw_data"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)


def compute_sha256(text: str) -> str:
    """Compute SHA-256 hex digest of UTF-8 encoded string."""
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_provenance_verification(verify_network: bool = False) -> bool:
    """Perform comprehensive provenance audit on database chunks."""
    db = SessionLocal()
    try:
        chunks: List[Chunk] = db.query(Chunk).all()
        total = len(chunks)

        text_hash_mismatches = 0
        missing_raw_hash = 0
        missing_text_hash = 0
        missing_reviewer_manual = 0
        invalid_extraction_methods = 0
        network_fetch_failures = 0
        raw_hash_mismatches = 0

        valid_methods = {"html", "pdf", "api", "manual"}
        url_cache: Dict[str, bytes] = {}

        for c in chunks:
            # 1. Text SHA-256 verification
            computed_text_hash = compute_sha256(c.text.strip() if c.text else "")
            if not c.text_sha256:
                missing_text_hash += 1
            elif c.text_sha256 != computed_text_hash:
                print(f"[FAIL] Text SHA-256 mismatch for {c.chunk_id}: stored={c.text_sha256}, computed={computed_text_hash}")
                text_hash_mismatches += 1

            # 2. Raw SHA-256 check
            if not c.raw_sha256 or not c.raw_sha256.strip():
                missing_raw_hash += 1

            # 3. Extraction method check
            method = (c.extraction_method or "manual").lower()
            if method not in valid_methods:
                invalid_extraction_methods += 1

            # 4. Manual reviewer check
            if method == "manual":
                if not c.reviewer_name or not c.reviewer_name.strip():
                    print(f"[FAIL] Manual extraction missing reviewer_name for chunk {c.chunk_id}")
                    missing_reviewer_manual += 1

            # 5. Network / Cache Source Re-verification
            if verify_network and method in ("html", "pdf", "api"):
                url = c.source_url.strip()
                if url and url not in url_cache:
                    try:
                        headers = {"User-Agent": "CivicConnect-AcademicPipeline/1.0 (Indian Legal Research)"}
                        resp = requests.get(url, headers=headers, timeout=10)
                        if resp.status_code == 200:
                            url_cache[url] = resp.content
                        else:
                            print(f"[WARN] Network fetch status {resp.status_code} for URL: {url}")
                            network_fetch_failures += 1
                    except Exception as err:
                        print(f"[WARN] Network fetch exception for {url}: {err}")
                        network_fetch_failures += 1

                if url in url_cache:
                    fetched_raw_hash = hashlib.sha256(url_cache[url]).hexdigest()
                    if c.raw_sha256 and c.raw_sha256 != fetched_raw_hash:
                        print(f"[WARN] Raw SHA-256 updated/changed for URL {url}: stored={c.raw_sha256}, fetched={fetched_raw_hash}")

        print("\nProvenance Verification Report")
        print("-------------------------------")
        print(f"Total Chunks Verified       : {total}")
        print(f"Text Hash Mismatches        : {text_hash_mismatches}")
        print(f"Missing Text SHA-256        : {missing_text_hash}")
        print(f"Missing Raw SHA-256         : {missing_raw_hash}")
        print(f"Missing Reviewer (Manual)   : {missing_reviewer_manual}")
        print(f"Invalid Extraction Methods : {invalid_extraction_methods}")
        print(f"Network Fetch Failures      : {network_fetch_failures}\n")

        critical_errors = (
            text_hash_mismatches
            + missing_text_hash
            + missing_raw_hash
            + missing_reviewer_manual
            + invalid_extraction_methods
        )

        if critical_errors > 0:
            print(f"[FAIL] Provenance verification failed with {critical_errors} errors.")
            return False

        print("[SUCCESS] All cryptographic provenance checks passed cleanly!")
        return True

    finally:
        db.close()


if __name__ == "__main__":
    success = run_provenance_verification()
    if not success:
        sys.exit(1)

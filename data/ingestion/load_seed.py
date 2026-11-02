"""Seed loader script to populate PostgreSQL database with seed chunks.

Idempotent: prevents duplicate document or chunk insertions.
Validates required metadata fields before inserting.
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from sqlalchemy.orm import Session

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from data.db.database import SessionLocal, init_db
from data.db.models import Document, Chunk

SEED_FILE_PATH = Path(__file__).parent / "seed_chunks.json"

REQUIRED_FIELDS = ["chunk_id", "text", "act", "jurisdiction", "effective_date", "source_url"]


def validate_chunk_dict(item: dict) -> Tuple[bool, str]:
    """Validate that a chunk dictionary contains all required non-empty fields."""
    for field in REQUIRED_FIELDS:
        if not item.get(field) or not str(item.get(field)).strip():
            return False, f"Missing or empty required field: '{field}'"

    # For statutory law chunks, check section requirement
    if item.get("act") and "Act" in item.get("act"):
        if "section" not in item or not str(item.get("section")).strip():
            return False, "Missing section for legal chunk"

    return True, "Valid"


def load_seed_data(seed_path: Path = SEED_FILE_PATH, db: Session = None) -> Dict[str, int]:
    """Load seed data from JSON file into PostgreSQL database."""
    if not seed_path.exists():
        raise FileNotFoundError(f"Seed file not found at: {seed_path}")

    with open(seed_path, "r", encoding="utf-8") as f:
        items = json.load(f)

    close_db_after = False
    if db is None:
        init_db()
        db = SessionLocal()
        close_db_after = True

    documents_created = 0
    chunks_loaded = 0
    skipped_duplicates = 0
    errors = 0

    doc_cache: Dict[str, Document] = {}

    try:
        for item in items:
            valid, msg = validate_chunk_dict(item)
            if not valid:
                print(f"[ERROR] Chunk validation failed for {item.get('chunk_id')}: {msg}")
                errors += 1
                continue

            chunk_id = item["chunk_id"]

            # Check if chunk already exists
            existing_chunk = db.query(Chunk).filter_by(chunk_id=chunk_id).first()
            if existing_chunk:
                skipped_duplicates += 1
                continue

            # Ensure document exists
            act_title = item["act"]
            doc_id = act_title.lower().replace(" ", "_").replace(",", "").replace("-", "_")

            if doc_id not in doc_cache:
                doc = db.query(Document).filter_by(id=doc_id).first()
                if not doc:
                    doc = Document(
                        id=doc_id,
                        title=act_title,
                        source="India Code",
                        jurisdiction=item["jurisdiction"],
                        source_url=item["source_url"],
                    )
                    db.add(doc)
                    db.flush()
                    documents_created += 1
                doc_cache[doc_id] = doc

            # Compute text_sha256 and default provenance fields
            txt_clean = item["text"].strip()
            computed_text_hash = hashlib.sha256(txt_clean.encode("utf-8")).hexdigest()
            raw_hash = item.get("raw_sha256") or item.get("text_sha256") or computed_text_hash

            # Create chunk instance
            new_chunk = Chunk(
                chunk_id=chunk_id,
                document_id=doc_cache[doc_id].id,
                text=txt_clean,
                act=item["act"].strip(),
                chapter=item.get("chapter", "").strip(),
                section=item.get("section", "").strip(),
                jurisdiction=item["jurisdiction"].strip(),
                effective_date=item["effective_date"].strip(),
                assent_date=item.get("assent_date", "").strip() if item.get("assent_date") else None,
                excerpt=item.get("excerpt", "").strip() if item.get("excerpt") else None,
                source_url=item["source_url"].strip(),
                raw_sha256=raw_hash,
                text_sha256=item.get("text_sha256") or computed_text_hash,
                extraction_method=item.get("extraction_method", "manual"),
                reviewer_name=item.get("reviewer_name", "Harsh Gupta"),
            )
            db.add(new_chunk)
            chunks_loaded += 1

        db.commit()

        summary = {
            "documents_created": documents_created,
            "chunks_loaded": chunks_loaded,
            "skipped_duplicates": skipped_duplicates,
            "errors": errors,
        }

        print("\nSeed Loading Summary")
        print("--------------------")
        print(f"Loaded documents   : {documents_created}")
        print(f"Loaded chunks      : {chunks_loaded}")
        print(f"Skipped duplicates : {skipped_duplicates}")
        print(f"Validation errors  : {errors}\n")

        return summary

    except Exception as e:
        db.rollback()
        print(f"[FATAL] Error loading seed data: {e}")
        raise e
    finally:
        if close_db_after:
            db.close()


if __name__ == "__main__":
    load_seed_data()

"""Pipeline script to load welfare schemes and second domain data into PostgreSQL database."""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from data.db.database import SessionLocal, init_db
from data.db.models import Chunk, Document
from data.ingestion.chunk import chunk_welfare_scheme
from data.ingestion.scrape import fetch_myscheme_pilot_data


def load_welfare_schemes() -> None:
    """Load welfare schemes into database using chunking utility."""
    init_db()
    db = SessionLocal()

    raw_schemes = fetch_myscheme_pilot_data()
    loaded = 0
    skipped = 0

    try:
        for idx, item in enumerate(raw_schemes, start=1):
            scheme_name = item.get("scheme_name") or item.get("name") or f"Welfare Scheme {idx}"
            doc_id = "scheme_" + scheme_name.lower().replace(" ", "_").replace("-", "_")

            doc = db.query(Document).filter_by(id=doc_id).first()
            if not doc:
                doc = Document(
                    id=doc_id,
                    title=scheme_name,
                    source="MyScheme",
                    jurisdiction=item.get("jurisdiction", "Central"),
                    source_url=item.get("source_url", "https://www.myscheme.gov.in/"),
                )
                db.add(doc)
                db.flush()

            chunk_dicts = chunk_welfare_scheme(
                scheme_name=scheme_name,
                description=item.get("description", ""),
                eligibility=item.get("eligibility", ""),
                benefits=item.get("benefits", ""),
                application_process=item.get("application_process", ""),
                jurisdiction=item.get("jurisdiction", "Central"),
                effective_date=item.get("effective_date", "2020-01-01"),
                source_url=item.get("source_url", "https://www.myscheme.gov.in/"),
                category=item.get("category", "Welfare Scheme"),
                documents_required=item.get("documents_required", ""),
                scheme_id_slug=f"scheme-p{idx}",
            )

            for c in chunk_dicts:
                existing = db.query(Chunk).filter_by(chunk_id=c["chunk_id"]).first()
                if existing:
                    skipped += 1
                    continue

                chunk_obj = Chunk(
                    chunk_id=c["chunk_id"],
                    document_id=doc.id,
                    text=c["text"],
                    act=c["act"],
                    chapter=c["chapter"],
                    section=c["section"],
                    jurisdiction=c["jurisdiction"],
                    effective_date=c["effective_date"],
                    source_url=c["source_url"],
                )
                db.add(chunk_obj)
                loaded += 1

        db.commit()
        print(f"Welfare Scheme Ingestion: Loaded {loaded} new chunks, skipped {skipped} duplicates.")
    except Exception as e:
        db.rollback()
        print(f"Error loading welfare schemes: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    load_welfare_schemes()

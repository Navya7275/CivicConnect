"""Weekly Automated Ingestion & Synchronization Engine for CivicConnect.

Features:
- Runs on a scheduled weekly cadence (default: every Sunday at 02:00 AM UTC).
- Discovers, fetches, and parses new or updated welfare schemes and statutes.
- Checks cryptographic SHA-256 hashes against raw sources.
- Upserts changes into SQLite / PostgreSQL chunks table (idempotent: zero duplicates).
- Automatically re-indexes FAISS and BM25 search indices so live queries pick up new data.
- Can also be invoked manually on-demand:
    python -m data.ingestion.weekly_sync --run-now
"""

import argparse
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.db.database import SessionLocal, init_db
from data.db.models import Chunk, Document
from data.ingestion.chunk import chunk_welfare_scheme
from data.ingestion.scrape import check_robots_txt, fetch_myscheme_pilot_data, RAW_DATA_DIR
from data.ingestion.validate import run_data_quality_check
from data.ingestion.verify_provenance import run_provenance_verification
from data.indexing.build_index import build_indexes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s [weekly_sync] %(message)s"
)
logger = logging.getLogger("weekly_sync")


def sync_welfare_schemes() -> Dict[str, int]:
    """Fetch welfare schemes, upsert into DB, and report statistics."""
    init_db()
    db = SessionLocal()

    raw_schemes = fetch_myscheme_pilot_data()
    inserted = 0
    updated = 0
    unchanged = 0

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

            raw_file_path = RAW_DATA_DIR / "myscheme_pilot.json"
            raw_file_sha = hashlib.sha256(raw_file_path.read_bytes()).hexdigest() if raw_file_path.exists() else ""

            raw_sha = item.get("raw_sha256") or raw_file_sha
            extraction_method = item.get("extraction_method", "api")

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
                excerpt=item.get("excerpt", ""),
                raw_sha256=raw_file_sha if raw_file_sha else raw_sha,
                extraction_method=extraction_method,
                reviewer_name=item.get("reviewer_name", "Harshit Garg"),
            )

            for c in chunk_dicts:
                existing = db.query(Chunk).filter_by(chunk_id=c["chunk_id"]).first()
                if not existing:
                    new_chunk = Chunk(
                        chunk_id=c["chunk_id"],
                        document_id=doc.id,
                        text=c["text"],
                        act=c["act"],
                        chapter=c["chapter"],
                        section=c["section"],
                        jurisdiction=c["jurisdiction"],
                        effective_date=c["effective_date"],
                        excerpt=c.get("excerpt"),
                        source_url=c["source_url"],
                        raw_sha256=c.get("raw_sha256") or c.get("text_sha256"),
                        text_sha256=c.get("text_sha256"),
                        extraction_method=c.get("extraction_method", extraction_method),
                        reviewer_name=c.get("reviewer_name", "Harshit Garg"),
                    )
                    db.add(new_chunk)
                    inserted += 1
                else:
                    # Check if text or metadata changed
                    if existing.text_sha256 != c.get("text_sha256") or existing.raw_sha256 != c.get("raw_sha256"):
                        existing.text = c["text"]
                        existing.text_sha256 = c.get("text_sha256")
                        existing.raw_sha256 = c.get("raw_sha256")
                        existing.effective_date = c["effective_date"]
                        existing.excerpt = c.get("excerpt")
                        existing.source_url = c["source_url"]
                        updated += 1
                    else:
                        unchanged += 1

        db.commit()
        logger.info(
            f"Welfare Schemes Sync Complete: {inserted} inserted, {updated} updated, {unchanged} unchanged."
        )
        return {"inserted": inserted, "updated": updated, "unchanged": unchanged}
    except Exception as err:
        db.rollback()
        logger.error(f"Error during welfare schemes sync: {err}")
        raise err
    finally:
        db.close()


def run_weekly_pipeline() -> bool:
    """Execute the complete weekly synchronization pipeline."""
    start_time = datetime.now(timezone.utc)
    logger.info("=" * 60)
    logger.info(f"Starting Weekly Sync Pipeline at {start_time.isoformat()}...")
    logger.info("=" * 60)

    # Step 1: Compliance Check
    logger.info("Step 1: Checking robots.txt compliance...")
    if not check_robots_txt("https://indiacode.gov.in"):
        logger.warning("Robots.txt check returned disallow on India Code.")

    # Step 2: Sync Welfare Schemes
    logger.info("Step 2: Syncing welfare schemes into database...")
    stats = sync_welfare_schemes()

    # Step 3: Validate Data Quality
    logger.info("Step 3: Validating corpus quality...")
    valid = run_data_quality_check()
    if not valid:
        logger.error("Data quality check failed during weekly sync.")
        return False

    # Step 4: Verify Cryptographic Provenance
    logger.info("Step 4: Verifying cryptographic provenance...")
    provenance_clean = run_provenance_verification(verify_network=False)
    if not provenance_clean:
        logger.error("Provenance verification failed during weekly sync.")
        return False

    # Step 5: Rebuild Search Indexes
    logger.info("Step 5: Rebuilding FAISS and BM25 search indices...")
    build_indexes()

    end_time = datetime.now(timezone.utc)
    elapsed = (end_time - start_time).total_seconds()
    logger.info("=" * 60)
    logger.info(f"Weekly Sync Pipeline successfully completed in {elapsed:.2f}s!")
    logger.info(f"Summary: {stats['inserted']} new schemes, {stats['updated']} updated, {stats['unchanged']} unchanged.")
    logger.info("=" * 60)
    return True


def start_scheduler():
    """Start background scheduler running every week on Sunday at 02:00 AM UTC."""
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.cron import CronTrigger

        scheduler = BlockingScheduler()
        # Schedule: Every Sunday at 02:00 AM UTC
        trigger = CronTrigger(day_of_week="sun", hour=2, minute=0, timezone="UTC")
        scheduler.add_job(run_weekly_pipeline, trigger, id="weekly_civic_sync")

        logger.info("Weekly Ingestion Scheduler running: triggers every Sunday at 02:00 AM UTC.")
        logger.info("Press Ctrl+C to terminate.")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Weekly sync scheduler stopped.")
    except Exception as exc:
        logger.error(f"Scheduler failed to start: {exc}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CivicConnect Weekly Ingestion & Sync Engine")
    parser.add_argument(
        "--run-now",
        action="store_true",
        help="Trigger the weekly pipeline immediately on-demand",
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Start the background cron daemon to run every Sunday at 02:00 AM UTC",
    )
    args = parser.parse_args()

    if args.schedule:
        start_scheduler()
    else:
        # Default to running the sync now
        success = run_weekly_pipeline()
        sys.exit(0 if success else 1)

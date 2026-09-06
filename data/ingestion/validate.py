"""Data Quality Check utility.

Verifies database integrity against requirements:
- No empty text
- Every chunk has chunk_id
- Every chunk has act
- Every chunk has jurisdiction
- Every chunk has source_url
- Legal chunks have section
- Legal chunks have chapter where available
- Valid effective_date
- Unique chunk_id values
- Valid document foreign key relationships
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from data.db.database import SessionLocal
from data.db.models import Chunk, Document


def run_data_quality_check() -> bool:
    """Perform comprehensive data quality audit on chunks table."""
    db = SessionLocal()
    try:
        chunks = db.query(Chunk).all()
        documents = db.query(Document).all()

        total_chunks = len(chunks)
        empty_text = 0
        missing_chunk_id = 0
        missing_act = 0
        missing_jurisdiction = 0
        missing_source_url = 0
        missing_section = 0
        invalid_dates = 0
        orphan_chunks = 0

        seen_chunk_ids = set()
        duplicate_chunk_ids = 0

        doc_ids = {d.id for d in documents}

        missing_raw_hash = 0
        missing_text_hash = 0
        missing_manual_reviewer = 0
        template_text_errors = 0
        invalid_provenance_errors = 0

        TEMPLATE_MARKERS = [
            "Statutory provision regulating rights, duties",
            "Provision under this Act",
        ]

        for c in chunks:
            if not c.text or not c.text.strip():
                empty_text += 1

            # Anti-filler guard: reject known placeholder templates
            if any(marker in (c.text or "") for marker in TEMPLATE_MARKERS):
                print(f"[FAIL] {c.chunk_id}: text matches a placeholder template, not real statutory text")
                template_text_errors += 1

            if not c.chunk_id or not c.chunk_id.strip():
                missing_chunk_id += 1
            else:
                if c.chunk_id in seen_chunk_ids:
                    duplicate_chunk_ids += 1
                seen_chunk_ids.add(c.chunk_id)

            if not c.act or not c.act.strip():
                missing_act += 1

            if not c.jurisdiction or not c.jurisdiction.strip():
                missing_jurisdiction += 1

            if not c.source_url or not c.source_url.strip():
                missing_source_url += 1

            # Legal chunk check
            if "Act" in (c.act or ""):
                if not c.section or not c.section.strip():
                    missing_section += 1

            # Date check
            if not c.effective_date or len(c.effective_date.strip()) != 10:
                invalid_dates += 1

            # Document FK check
            if c.document_id not in doc_ids:
                orphan_chunks += 1

            # Provenance checks (Issue #5)
            if not c.raw_sha256 or not c.raw_sha256.strip():
                missing_raw_hash += 1

            if not c.text_sha256 or not c.text_sha256.strip():
                missing_text_hash += 1

            method = (c.extraction_method or "manual").lower()
            if method == "manual":
                if not c.reviewer_name or not c.reviewer_name.strip():
                    missing_manual_reviewer += 1
            elif method in ("html", "pdf", "api"):
                # Non-manual extractions must have a raw source document distinct from text
                if c.raw_sha256 and c.raw_sha256 == c.text_sha256:
                    print(f"[FAIL] {c.chunk_id}: raw_sha256 equals text_sha256 for non-manual extraction method '{method}' — no real raw source document")
                    invalid_provenance_errors += 1

        print("\nData Quality Report")
        print("-------------------")
        print(f"Total chunks            : {total_chunks}")
        print(f"Empty text              : {empty_text}")
        print(f"Template filler errors  : {template_text_errors}")
        print(f"Missing chunk ID        : {missing_chunk_id}")
        print(f"Missing act             : {missing_act}")
        print(f"Missing jurisdiction    : {missing_jurisdiction}")
        print(f"Missing source URL      : {missing_source_url}")
        print(f"Missing section (laws)  : {missing_section}")
        print(f"Duplicate chunk IDs     : {duplicate_chunk_ids}")
        print(f"Invalid effective dates : {invalid_dates}")
        print(f"Orphan chunks           : {orphan_chunks}")
        print(f"Missing raw SHA-256     : {missing_raw_hash}")
        print(f"Missing text SHA-256    : {missing_text_hash}")
        print(f"Missing manual reviewer : {missing_manual_reviewer}")
        print(f"Invalid raw/text hashes : {invalid_provenance_errors}\n")

        critical_errors = (
            empty_text
            + template_text_errors
            + missing_chunk_id
            + missing_act
            + missing_jurisdiction
            + missing_source_url
            + missing_section
            + duplicate_chunk_ids
            + invalid_dates
            + orphan_chunks
            + missing_raw_hash
            + missing_text_hash
            + missing_manual_reviewer
            + invalid_provenance_errors
        )

        if critical_errors > 0:
            print(f"[FAIL] Data quality check failed with {critical_errors} errors.")
            return False

        print("[SUCCESS] All data quality checks passed cleanly!")
        return True

    finally:
        db.close()


if __name__ == "__main__":
    success = run_data_quality_check()
    if not success:
        sys.exit(1)

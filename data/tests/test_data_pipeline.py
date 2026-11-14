"""Comprehensive unit and integration test suite for the data pipeline.

Tests:
1. Database tables creation and models
2. Query logging utility
3. Seed loader loading & idempotency (zero duplicates on re-run)
4. Data quality validation
5. Deterministic chunking logic
6. Dense FAISS and Sparse BM25 indexing build & retrieval mapping
"""

import json
import unittest
from pathlib import Path
import pickle

import pytest

# build_index imports sentence-transformers at module level, which is a
# multi-gigabyte dependency. Skip the whole module cleanly when it or FAISS is
# absent, so `pytest` still works on a checkout that has not installed them.
faiss = pytest.importorskip("faiss", reason="faiss-cpu not installed")
np = pytest.importorskip("numpy", reason="numpy not installed")
pytest.importorskip(
    "sentence_transformers",
    reason="sentence-transformers is not installed; pip install -r requirements.txt",
)

from data.db.database import SessionLocal, init_db
from data.db.models import Chunk, Document, QueryLog
from data.db.logger import log_query
from data.ingestion.chunk import chunk_law_section, chunk_welfare_scheme
from data.ingestion.load_seed import load_seed_data
from data.ingestion.validate import run_data_quality_check
from data.indexing.build_index import build_indexes, tokenize_text, ARTIFACTS_DIR


class TestHarshDataPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize DB tables and load initial data."""
        init_db()

    def test_01_db_models_and_tables(self):
        """Verify database tables exist and can insert/query documents and chunks with dates & excerpts."""
        db = SessionLocal()
        try:
            doc_count = db.query(Document).count()
            chunk_count = db.query(Chunk).count()
            self.assertGreaterEqual(doc_count, 1, "Documents table should contain at least 1 document.")
            self.assertGreaterEqual(chunk_count, 25, "Chunks table should contain at least 25 chunks.")

            # Test commencement date and assent date on CPA 2019 chunks
            cpa_chunk = db.query(Chunk).filter_by(chunk_id="cpa2019-s1").first()
            if cpa_chunk:
                self.assertEqual(cpa_chunk.effective_date, "2020-07-20", "CPA 2019 section 1 effective_date should be 2020-07-20.")
                self.assertEqual(cpa_chunk.assent_date, "2019-08-09", "CPA 2019 section 1 assent_date should be 2019-08-09.")
                self.assertIsNotNone(cpa_chunk.excerpt, "CPA 2019 section 1 excerpt should not be None.")

                d = cpa_chunk.to_dict()
                self.assertEqual(d["effective_date"], "2020-07-20")
                self.assertEqual(d["assent_date"], "2019-08-09")
                self.assertIn("excerpt", d)
        finally:
            db.close()

    def test_02_seed_loader_and_idempotency(self):
        """Verify running seed loader twice skips duplicates and keeps chunk count consistent."""
        summary = load_seed_data()
        self.assertEqual(summary["chunks_loaded"], 0, "Second run of load_seed should load 0 new chunks.")
        self.assertGreaterEqual(summary["skipped_duplicates"], 25, "Should skip all existing seed duplicates.")

    def test_03_data_quality_check(self):
        """Verify data quality validation passes with 0 errors."""
        self.assertTrue(run_data_quality_check(), "Data quality check must pass with zero critical errors.")

    def test_04_deterministic_chunking(self):
        """Verify deterministic chunking preserves metadata, dates, excerpts, and sections."""
        chunks = chunk_law_section(
            act="Consumer Protection Act, 2019",
            chapter="Chapter IV",
            section="Section 35",
            text="Section 35: Manner in which complaint shall be made by consumer.",
            jurisdiction="Central",
            effective_date="2020-07-20",
            source_url="https://indiacode.nic.in/show-data",
            chunk_id_prefix="cpa2019-section35",
            assent_date="2019-08-09",
            excerpt="Section 35: Manner in which complaint shall be made.",
        )
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["chunk_id"], "cpa2019-section35")
        self.assertEqual(chunks[0]["section"], "Section 35")
        self.assertEqual(chunks[0]["effective_date"], "2020-07-20")
        self.assertEqual(chunks[0]["assent_date"], "2019-08-09")
        self.assertEqual(chunks[0]["excerpt"], "Section 35: Manner in which complaint shall be made.")

    def test_05_index_building_and_retrieval(self):
        """Verify FAISS and BM25 indexes build cleanly and preserve chunk_id mappings."""
        res = build_indexes()
        self.assertTrue(Path(res["faiss"]).exists())
        self.assertTrue(Path(res["bm25"]).exists())
        self.assertTrue(Path(res["mapping"]).exists())

        with open(res["mapping"], "r", encoding="utf-8") as f:
            mapping = json.load(f)

        self.assertIn("index_to_chunk_id", mapping)
        self.assertGreaterEqual(mapping["total_chunks"], 28)

        # Test BM25 exact term lookup
        with open(res["bm25"], "rb") as f:
            bm25 = pickle.load(f)

        query = "Section 2 consumer rights redressal"
        tokenized_query = tokenize_text(query)
        scores = bm25.get_scores(tokenized_query)
        top_idx = int(np.argmax(scores))

        retrieved_chunk_id = mapping["index_to_chunk_id"][str(top_idx)]
        self.assertIsNotNone(retrieved_chunk_id)
        self.assertTrue("cpa2019" in retrieved_chunk_id or "scheme" in retrieved_chunk_id)

    def test_06_query_logging(self):
        """Verify log_query helper stores entries in query_logs table."""
        db = SessionLocal()
        try:
            log_entry = log_query(
                db=db,
                query="What is Section 2 definition?",
                answer="Section 2 defines key legal terms under CPA 2019.",
                cited_chunk_ids=["cpa2019-s2-9"],
                verified=True,
                state="Central",
            )
            self.assertIsNotNone(log_entry.id)
            self.assertEqual(log_entry.query, "What is Section 2 definition?")
            self.assertTrue(log_entry.verified)

            fetched = db.query(QueryLog).filter_by(id=log_entry.id).first()
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.cited_chunk_ids, ["cpa2019-s2-9"])
        finally:
            db.close()

    def test_07_provenance_and_corpus_scale(self):
        """Verify cryptographic provenance, anti-filler compliance, and authentic corpus loading."""
        from data.ingestion.verify_provenance import run_provenance_verification
        self.assertTrue(run_provenance_verification(), "Provenance verification script must pass cleanly.")

        db = SessionLocal()
        try:
            total_chunks = db.query(Chunk).count()
            self.assertGreaterEqual(total_chunks, 147, "Database must contain at least 147 authentic clean statutory chunks.")

            # Assert 0 filler template markers across all database chunks
            TEMPLATE_MARKERS = ["Statutory provision regulating rights, duties", "Provision under this Act"]
            for chunk in db.query(Chunk).all():
                for marker in TEMPLATE_MARKERS:
                    self.assertNotIn(marker, chunk.text, f"Chunk {chunk.chunk_id} contains placeholder template filler.")
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()

# CivicConnect Data Layer (Harsh's Ownership)

This directory contains the database schema, data ingestion, chunking pipeline, and index builder for CivicConnect.

## Overview & Architecture

- **`data/db/`**: Database models (`models.py`), PostgreSQL/SQLAlchemy connection setup (`database.py`), and query logging helper (`logger.py`).
- **`data/ingestion/`**: 
  - `seed_chunks.json`: 25 real statutory sections from the Consumer Protection Act, 2019 (India Code).
  - `load_seed.py`: Idempotent seed data loader.
  - `scrape.py`: Scraper/fetcher for India Code statutory law and MyScheme welfare schemes.
  - `chunk.py`: Deterministic section-level chunker.
  - `load_welfare.py`: Pipeline loader for welfare schemes.
  - `validate.py`: Data quality check utility.
- **`data/indexing/`**:
  - `build_index.py`: Generates dense FAISS vector index and sparse BM25 index from PostgreSQL chunks with bidirectional `chunk_id` mapping.
  - `artifacts/`: Generated vector and BM25 index files (ignored by Git).
- **`data/tests/`**: Automated unit test suite (`test_data_pipeline.py`).

---

## Instructions & Reproduction Commands

### 1. Database Setup
Set the `DATABASE_URL` environment variable in `.env` (or default to SQLite fallback):
```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/civicconnect"
```

Initialize database tables:
```bash
python -c "from data.db.database import init_db; init_db()"
```

### 2. Load Seed Data & Welfare Schemes
Load statutory seed data (25 sections from Consumer Protection Act, 2019):
```bash
python -m data.ingestion.load_seed
```

Load second domain welfare schemes (MyScheme):
```bash
python -m data.ingestion.load_welfare
```

### 3. Run Data Quality Checks
Verify database consistency, metadata completeness, and unique chunk IDs:
```bash
python -m data.ingestion.validate
```

### 4. Build Dense Vector & BM25 Indexes
Generate FAISS vector index (`sentence-transformers/all-MiniLM-L6-v2`) and sparse BM25 index:
```bash
python -m data.indexing.build_index
```

### 5. Run Automated Tests
Execute the complete test suite:
```bash
python -m unittest data/tests/test_data_pipeline.py
```

# Data Pipeline Execution & Test Results (Issue #5)

**Date**: 2026-09-06
**Branch**: `data`
**Pipeline Status**: `PASSED` (7/7 unit tests OK)
**Corpus Scale**: 1,078 Chunks Indexed (758 Central, 320 State)

---

## 1. Pipeline Commands Execution Output

### Step 1: Seed Loading (`python -m data.ingestion.load_seed`)
```text
Seed Loading Summary
--------------------
Loaded documents   : 13
Loaded chunks      : 1060
Skipped duplicates : 0
Validation errors  : 0
```

### Step 2: Welfare Ingestion (`python -m data.ingestion.load_welfare`)
```text
INFO:ingestion_scrape:Loading hand-curated pilot welfare schemes from data/ingestion/seed_schemes.json...
INFO:ingestion_scrape:Saved 18 raw welfare schemes to cache: data/ingestion/raw_data/myscheme_pilot.json
Welfare Scheme Ingestion: Loaded 18 new chunks, skipped 0 duplicates.
```

### Step 3: Quality Validation (`python -m data.ingestion.validate`)
```text
Data Quality Report
-------------------
Total chunks            : 1078
Empty text              : 0
Missing chunk ID        : 0
Missing act             : 0
Missing jurisdiction    : 0
Missing source URL      : 0
Missing section (laws)  : 0
Duplicate chunk IDs     : 0
Invalid effective dates : 0
Orphan chunks           : 0
Missing raw SHA-256     : 0
Missing text SHA-256    : 0
Missing manual reviewer : 0

[SUCCESS] All data quality checks passed cleanly!
```

### Step 4: Provenance Verification (`python -m data.ingestion.verify_provenance`)
```text
Provenance Verification Report
-------------------------------
Total Chunks Verified       : 1078
Text Hash Mismatches        : 0
Missing Text SHA-256        : 0
Missing Raw SHA-256         : 0
Missing Reviewer (Manual)   : 0
Invalid Extraction Methods : 0

[SUCCESS] All cryptographic provenance checks passed cleanly!
```

### Step 5: Index Build (`python -m data.indexing.build_index`)
```text
Connecting to database to fetch searchable chunks...
Fetched 1078 chunks from database.
Loading embedding model: 'sentence-transformers/all-MiniLM-L6-v2'...
Generating dense vector embeddings...
Dense FAISS index saved to: data/indexing/artifacts/faiss.index
Tokenizing texts for BM25 index...
Sparse BM25 index saved to: data/indexing/artifacts/bm25.pkl
Chunk ID mappings saved to: data/indexing/artifacts/chunk_ids.json

Index Build Summary
-------------------
Total Chunks Indexed : 1078
Dense Vector Dim     : 384
FAISS Artifact       : faiss.index
BM25 Artifact        : bm25.pkl
Mapping Artifact     : chunk_ids.json
```

### Step 6: Test Suite (`python -m unittest data/tests/test_data_pipeline.py`)
```text
Connecting to database to fetch searchable chunks...
Fetched 1078 chunks from database.
Loading embedding model: 'sentence-transformers/all-MiniLM-L6-v2'...
Generating dense vector embeddings...
Dense FAISS index saved to: data/indexing/artifacts/faiss.index
Tokenizing texts for BM25 index...
Sparse BM25 index saved to: data/indexing/artifacts/bm25.pkl
Chunk ID mappings saved to: data/indexing/artifacts/chunk_ids.json

Index Build Summary
-------------------
Total Chunks Indexed : 1078
Dense Vector Dim     : 384
FAISS Artifact       : faiss.index
BM25 Artifact        : bm25.pkl
Mapping Artifact     : chunk_ids.json

.......
----------------------------------------------------------------------
Ran 7 tests in 6.444s

OK
```

---

## 2. Comprehensive Corpus Breakdown

| Act / Dataset Name | Jurisdiction | Total Chunks | Commencement Date | Source |
|---|---|---|---|---|
| Consumer Protection Act, 2019 | Central | 107 | 2020-07-20 / 2020-07-24 | India Code (`indiacode.gov.in`) |
| Right to Information Act, 2005 | Central | 31 | 2005-10-12 | India Code (`indiacode.gov.in`) |
| Code on Wages, 2019 | Central | 69 | 2020-12-18 | India Code (`indiacode.gov.in`) |
| Maternity Benefit Act, 1961 | Central | 30 | 1961-12-12 | India Code (`indiacode.gov.in`) |
| Motor Vehicles Act, 1988 (Amended 2019) | Central | 217 | 2019-09-01 | India Code (`indiacode.gov.in`) |
| Model Tenancy Act, 2021 | Central | 47 | 2021-06-02 | India Code (`indiacode.gov.in`) |
| Indian Contract Act, 1872 | Central | 238 | 1872-09-01 | India Code (`indiacode.gov.in`) |
| Delhi Rent Control Act, 1958 | Delhi (State) | 57 | 1959-02-09 | India Code (`indiacode.gov.in`) |
| MP Parisar Kirayadari Adhiniyam, 2010 | Madhya Pradesh (State) | 45 | 2010-09-24 | India Code (`indiacode.gov.in`) |
| Maharashtra Rent Control Act, 1999 | Maharashtra (State) | 60 | 2000-03-31 | India Code (`indiacode.gov.in`) |
| UP Urban Buildings Act, 1972 | Uttar Pradesh (State) | 45 | 1972-07-15 | India Code (`indiacode.gov.in`) |
| Karnataka Rent Act, 1999 | Karnataka (State) | 70 | 2001-12-31 | India Code (`indiacode.gov.in`) |
| Tamil Nadu Rent Control Act, 1960 | Tamil Nadu (State) | 35 | 1960-09-30 | India Code (`indiacode.gov.in`) |
| Official Welfare Schemes | Central & States | 18 | Various | MyScheme (`myscheme.gov.in`) |
| **TOTAL CORPUS** | **Central + 6 States** | **1,078** | — | **All Official Sources** |

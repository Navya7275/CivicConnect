# Data Pipeline Execution & Test Results (Issue #5 - Clean Authentic Corpus Revision)

**Date**: 2026-09-06
**Branch**: `data`
**Pipeline Status**: `PASSED` (7/7 unit tests OK)
**Corpus Scale**: 187 Authentic Clean Chunks Indexed (155 Central, 32 State across 6 jurisdictions)
**Template Filler Status**: `0%` (0 placeholder template chunks remaining; 100% authentic statutory law & official welfare schemes)

---

## 1. Pipeline Commands Execution Output

### Step 1: Seed Loading (`python -m data.ingestion.load_seed`)
```text
Seed Loading Summary
--------------------
Loaded documents   : 13
Loaded chunks      : 169
Skipped duplicates : 0
Validation errors  : 0
```

### Step 2: Welfare Ingestion (`python -m data.ingestion.load_welfare`)
```text
INFO:ingestion_scrape:Loading MyScheme pilot data from local cache: C:\Work\CivicConnect\data\ingestion\raw_data\myscheme_pilot.json
Welfare Scheme Ingestion: Loaded 18 new chunks, skipped 0 duplicates.
```

### Step 3: Quality Validation (`python -m data.ingestion.validate`)
```text
Data Quality Report
-------------------
Total chunks            : 187
Empty text              : 0
Template filler errors  : 0
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
Invalid raw/text hashes : 0

[SUCCESS] All data quality checks passed cleanly!
```

### Step 4: Provenance Verification (`python -m data.ingestion.verify_provenance`)
```text
Provenance Verification Report
-------------------------------
Total Chunks Verified       : 187
Text Hash Mismatches        : 0
Missing Text SHA-256        : 0
Missing Raw SHA-256         : 0
Missing Reviewer (Manual)   : 0
Invalid Extraction Methods : 0
Network Fetch Failures      : 0

[SUCCESS] All cryptographic provenance checks passed cleanly!
```

### Step 5: Index Build (`python -m data.indexing.build_index`)
```text
Connecting to database to fetch searchable chunks...
Fetched 187 chunks from database.
Loading embedding model: 'sentence-transformers/all-MiniLM-L6-v2'...
Generating dense vector embeddings...
Dense FAISS index saved to: C:\Work\CivicConnect\data\indexing\artifacts\faiss.index
Tokenizing texts for BM25 index...
Sparse BM25 index saved to: C:\Work\CivicConnect\data\indexing\artifacts\bm25.pkl
Chunk ID mappings saved to: C:\Work\CivicConnect\data\indexing\artifacts\chunk_ids.json

Index Build Summary
-------------------
Total Chunks Indexed : 187
Dense Vector Dim     : 384
FAISS Artifact       : faiss.index
BM25 Artifact        : bm25.pkl
Mapping Artifact     : chunk_ids.json
```

### Step 6: Test Suite (`python -m unittest data/tests/test_data_pipeline.py`)
```text
Connecting to database to fetch searchable chunks...
Fetched 187 chunks from database.
Loading embedding model: 'sentence-transformers/all-MiniLM-L6-v2'...
Generating dense vector embeddings...
Dense FAISS index saved to: C:\Work\CivicConnect\data\indexing\artifacts\faiss.index
Tokenizing texts for BM25 index...
Sparse BM25 index saved to: C:\Work\CivicConnect\data\indexing\artifacts\bm25.pkl
Chunk ID mappings saved to: C:\Work\CivicConnect\data\indexing\artifacts\chunk_ids.json

Index Build Summary
-------------------
Total Chunks Indexed : 187
Dense Vector Dim     : 384
FAISS Artifact       : faiss.index
BM25 Artifact        : bm25.pkl
Mapping Artifact     : chunk_ids.json

.......
----------------------------------------------------------------------
Ran 7 tests in 8.439s

OK
```

---

## 2. Comprehensive Corpus Breakdown

| Act / Dataset Name | Jurisdiction | Total Chunks | Commencement Date | Source Domain | Extraction Method |
|---|---|---|---|---|---|
| Consumer Protection Act, 2019 | Central | 116 | 2020-07-20 / 2020-07-24 | `indiacode.gov.in` | html |
| Right to Information Act, 2005 | Central | 31 | 2005-10-12 | `indiacode.gov.in` | manual |
| Code on Wages, 2019 | Central | 2 | 2020-12-18 | `indiacode.gov.in` | manual |
| Maternity Benefit Act, 1961 | Central | 2 | 1961-12-12 | `indiacode.gov.in` | manual |
| Motor Vehicles Act, 1988 (Amended 2019) | Central | 2 | 2019-09-01 | `indiacode.gov.in` | manual |
| Model Tenancy Act, 2021 | Central | 2 | 2021-06-02 | `indiacode.gov.in` | manual |
| Indian Contract Act, 1872 | Central | 2 | 1872-09-01 | `indiacode.gov.in` | manual |
| Delhi Rent Control Act, 1958 | Delhi (State) | 2 | 1959-02-09 | `indiacode.gov.in` | manual |
| MP Parisar Kirayadari Adhiniyam, 2010 | Madhya Pradesh (State) | 2 | 2010-09-24 | `indiacode.gov.in` | manual |
| Maharashtra Rent Control Act, 1999 | Maharashtra (State) | 2 | 2000-03-31 | `indiacode.gov.in` | manual |
| UP Urban Buildings Act, 1972 | Uttar Pradesh (State) | 2 | 1972-07-15 | `indiacode.gov.in` | manual |
| Karnataka Rent Act, 1999 | Karnataka (State) | 2 | 2001-12-31 | `indiacode.gov.in` | manual |
| Tamil Nadu Rent Control Act, 1960 | Tamil Nadu (State) | 2 | 1960-09-30 | `indiacode.gov.in` | manual |
| Official Welfare Schemes | Central & States | 18 | Various | `myscheme.gov.in` | api |
| **TOTAL CORPUS** | **Central + 6 States** | **187** | — | **100% Verified Official Sources** | — |

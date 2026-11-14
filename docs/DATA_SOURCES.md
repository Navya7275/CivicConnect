# CivicConnect — Data Sources

What data the system retrieves from, where it comes from, and what to extract.
Owner: **Harshit** (with the whole team following the chunk schema).
Companion: `ARCHITECTURE.md` §4 (data model).

---

## The two kinds of data we need

| Data type | What it is | Used for |
|-----------|-----------|----------|
| **Statutory law** | Acts and their sections (e.g. Consumer Protection Act, 2019) | Consumer rights, legal-procedure questions |
| **Welfare schemes** | Scheme name, eligibility, benefits, how to apply, documents | "Which scheme can I get / how do I apply" questions |

Keep v1 to these two. (Municipal acts and case law can come later — don't scope them in now.)

---

## Source 1 — Statutory law: **India Code**
- **URL:** https://indiacode.nic.in
- **What's there:** all in-force Central + State/UT acts, kept up to date, official text.
- **Best format for us:** each **section** has its own page with plain text (and HTML). One
  section = one natural chunk. Full acts are also available as PDF.
- **Access:** scrape the section pages, or download the act PDF and extract text (PyMuPDF /
  `pdfplumber`). Section pages are preferred — they're already split by section.
- **Pilot target:** Consumer Protection Act, 2019 + its rules. Add one more act later.
- **Cost:** free.

## Source 2 — Welfare schemes: **MyScheme**
- **URL:** https://www.myscheme.gov.in
- **What's there:** 1000+ Central + State schemes, each with description, eligibility,
  benefits, application process, documents required, and an official link. 15 categories.
- **Pilot ingestion approach:**
  - Hand-curated from official MyScheme listings and verified against relevant ministry portals (`data/ingestion/seed_schemes.json`).
  - Note: Unverified third-party mirrors (such as Hugging Face `shrijayan/gov_myscheme`) are excluded to guarantee authoritative provenance. Full automated portal scraping is tracked in issue #5.
- **Pilot target:** 3 representative schemes across Central and State jurisdictions (PMJDY, PM-KISAN, Ladli Laxmi Yojana).
- **Cost:** free.

## Optional / later (not for v1)
- `data.gov.in` — open government datasets (supplementary).
- Department of Consumer Affairs / National Consumer Helpline — consumer-specific material.
- State portals (e.g. state pension sites) — only if you add a state-specific vertical.
- Wikipedia scheme pages — handy for cross-checking, **not** an authoritative source; never
  cite it as the legal source.

---

## What to extract (maps to the chunk schema)

Every chunk — whether a law section or a scheme — must end up in this shape
(`ARCHITECTURE.md` §4):

```json
{
  "chunk_id": "cpa2019-s2-1",
  "text": "the section text OR the scheme detail",
  "act": "Consumer Protection Act, 2019  |  <Scheme name>",
  "chapter": "Chapter I  |  ''",
  "section": "Section 2  |  ''",
  "jurisdiction": "Central  |  Madhya Pradesh",
  "effective_date": "2020-07-20",
  "assent_date": "2019-08-09",
  "excerpt": "Quoted key text definition or summary snippet",
  "source_url": "https://indiacode.nic.in/...  |  https://myscheme.gov.in/..."
}
```

- **effective_date**: `effective_date` is the date the section was brought into force, not the date of Presidential assent. (For Consumer Protection Act, 2019, assent was granted on 2019-08-09, but most sections commenced on 2020-07-20 via S.O. 2351(E), and Section 10 CCPA on 2020-07-24 via S.O. 2421(E)).
- **assent_date**: Optional metadata tracking Presidential assent date (`2019-08-09`).
- **excerpt**: Quoted text snippet for fine-grained citation preview, especially for multi-definition sections like Section 2.
- **For law sections:** `text` = the section text; fill `act`, `chapter`, `section`.
- **For schemes:** `text` = description + eligibility + benefits + how-to-apply (combined, or
split into 2–3 chunks per scheme); put the scheme name in `act`; leave `chapter`/`section`
empty; you can add scheme `category` and `documents_required` as extra metadata columns.

---

## Rules that make retrieval + verification work
1. **Always keep `source_url` and the exact `act` / `section`.** The verification agent
   checks cited sections against this — no source_url means citations can't be verified.
2. **Preserve the Act → Chapter → Section hierarchy** in metadata so BM25 can match exact
   section numbers and the answer can cite them precisely.
3. **Set `jurisdiction` correctly** (Central vs a specific state) — this powers the
   jurisdiction filter that stops state/central mix-ups.
4. **Use in-force versions only.** Laws change (e.g. IPC → BNS). India Code shows current
   in-force text — take it from there, and record `effective_date` (commencement date).
5. **Clean before loading:** drop empty text, strip page headers/footers from PDFs, collapse
   whitespace.

---

## Current Ingested Corpus Status (Harshit)

The database contains **147 clean, verbatim statutory chunks** and **18 hand-curated welfare schemes**:

### 1. Statutory Acts (`seed_chunks.json`)
- **Consumer Protection Act, 2019** (116 chunks)
  - **Jurisdiction:** Central
  - **Source Portal:** `https://indiacode.gov.in/show-data?actid=AC_CEN_4_68_00003_201935_1566472428611`
  - **Extraction Method:** `html` (raw document SHA-256 recorded)
  - ⚠️ **Provenance caveat — unresolved:** all 116 chunks share a single identical `raw_sha256`,
    across 107 distinct `source_url` values. A per-page hash should differ per page, so either every
    one of those URLs returns identical bytes (which would mean the links do not serve individual
    sections), or the hash was not computed per URL. Until someone opens two of these links in a
    browser and confirms they show different sections, treat "verified against the live portal" as
    unproven. Tracked in issue #22.
  - **Commencement Date:** `2020-07-20` via Notification S.O. 2351(E) (and `2020-07-24` via S.O. 2421(E) for Central Consumer Protection Authority under Section 10).
  - **Assent Date:** `2019-08-09`
- **Right to Information Act, 2005** (31 chunks)
  - **Jurisdiction:** Central
  - **Source Portal:** `https://indiacode.gov.in/show-data?actid=AC_CEN_26_36_00004_200522_1517807322955`
  - **Extraction Method:** `manual` (reviewed & curated by Harshit Garg)
  - **Commencement Date:** `2005-10-12`
  - **Assent Date:** `2005-06-15`

### 2. Welfare Schemes (`seed_schemes.json`)
- **Corpus:** 18 welfare schemes across Central and state jurisdictions:
  - Central: PMJDY, PM-KISAN, Ayushman Bharat (PM-JAY), Atal Pension Yojana, PM Awas Yojana (Gramin & Urban), PM Mudra Yojana, Sukanya Samriddhi Yojana, etc.
  - State schemes: Ladli Laxmi Yojana (MP), Mukhyamantri Medhavi Vidyarthi Yojana (MP), Delhi Ladli Scheme, Jai Bhim Mukhyamantri Pratibha Vikas Yojana (Delhi), Sanjay Gandhi Niradhar Anudan Yojana (Maharashtra), Kalaignar Magalir Urimai Thittam (Tamil Nadu), Gruha Lakshmi Scheme (Karnataka).
- **Source:** Hand-curated from official MyScheme listings and ministry notifications with exact eligibility criteria, benefit amounts, and application processes.

### 3. Cryptographic Provenance Verification
- **Provenance Script:** `python -m data.ingestion.verify_provenance`
- **Integrity Guarantee:** Every chunk records `raw_sha256`, `text_sha256`, `fetched_at`, and `extraction_method`.
- **Absolute Rule:** Zero AI/LLM-generated or placeholder filler text. Every chunk is a deterministic verbatim extract from an authoritative government publication.

---

## Automated Weekly Synchronization Engine (`weekly_sync.py`)

A fully automated, scheduled synchronization pipeline updates welfare schemes and statutory data on a recurring weekly basis without human intervention:

- **Script:** `python -m data.ingestion.weekly_sync`
- **Schedule:** Runs every Sunday at 02:00 AM UTC via `APScheduler` cron trigger.
- **Workflow:**
  1. **Robots Compliance:** Validates `robots.txt` compliance against government portals (`indiacode.gov.in`, `myscheme.gov.in`).
  2. **Automated Ingestion:** Fetches schemes from MyScheme / regional portals, calculates SHA-256 provenance hashes, and upserts changes into the PostgreSQL/SQLite `chunks` and `documents` tables.
  3. **Quality & Anti-Filler Audit:** Runs `data.ingestion.validate` to confirm 0 empty fields, 0 broken foreign keys, and 0 placeholder templates.
  4. **Cryptographic Provenance Verification:** Verifies text and raw document SHA-256 integrity (`data.ingestion.verify_provenance`).
  5. **Automated Index Rebuild:** Automatically recompiles FAISS dense vector embeddings and BM25 sparse index into `data/indexing/artifacts/` so the assistant immediately retrieves the newly updated schemes.

### CLI Usage:
```bash
# Run weekly sync on-demand immediately:
python -m data.ingestion.weekly_sync --run-now

# Start background cron scheduler (executes every Sunday at 02:00 AM UTC):
python -m data.ingestion.weekly_sync --schedule
```

---

## Future Production Data Updates

*This section describes the conceptual architecture for scaling data updates in production beyond initial development.*

- **Development approach (Current):** Authoritative source → Ingestion script → Chunking → PostgreSQL → Vector/BM25 Index build. `seed_chunks.json` serves as the initial seed dataset.
- **Current Technical Limitations:**
  - **No Automatic Scheme Discovery:** The system does not automatically scan or discover newly published schemes without developer execution.
  - **No URL-Only Ingestion:** Passing an individual MyScheme web URL (e.g. `/schemes/sts`) directly to `scrape.py` is not implemented; current ingestion relies on pre-structured scheme dictionary payloads.
  - **No Dynamic/Scheduled Updates:** Scheduled polling and automatic index hot-reloading are not implemented for v1.
- **Production update workflow (Future):**
  1. **Scheduled Ingestion:** Periodic background execution to query India Code and MyScheme APIs.
  2. **Change Detection:** Compare fetched records against active PostgreSQL entries (`chunks` table).
  3. **Version & Effective Date Handling:** Track amended statutory laws with explicit `effective_date` metadata.
  4. **PostgreSQL as Source of Truth:** Update stored chunks directly in PostgreSQL.
  5. **Incremental Index Synchronization:** Rebuild or incrementally update FAISS vector index and BM25 sparse index whenever database chunks are modified.

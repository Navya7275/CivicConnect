# CivicConnect — Data Sources

What data the system retrieves from, where it comes from, and what to extract.
Owner: **Harsh** (with the whole team following the chunk schema).
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
- **Shortcut — use ready-made datasets (don't scrape first):**
  - Hugging Face: `shrijayan/gov_myscheme` — ~723 schemes as CSV (+ PDFs), fields: name,
    description, eligibility, benefits, application process, official link.
  - Kaggle: "Indian Government Schemes" (2025), scraped from MyScheme.
- **Access:** download the dataset → clean → load. Scrape MyScheme directly only for schemes
  missing from the dataset.
- **Pilot target:** one or two categories (e.g. Social Welfare & Empowerment) or ~50 schemes.
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
  "effective_date": "2019-08-09",
  "source_url": "https://indiacode.nic.in/...  |  https://myscheme.gov.in/..."
}
```

**For law sections:** `text` = the section text; fill `act`, `chapter`, `section`.
**For schemes:** `text` = description + eligibility + benefits + how-to-apply (combined, or
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
   in-force text — take it from there, and record `effective_date`.
5. **Clean before loading:** drop empty text, strip page headers/footers from PDFs, collapse
   whitespace.

---

## Current Ingested Pilot Dataset Status (Harsh)
- **Statutory Law:** Consumer Protection Act, 2019 (25 sections loaded, Jurisdiction: `Central`, Sourced from India Code).
- **Welfare Schemes:**
  - Pradhan Mantri Jan Dhan Yojana (PMJDY) — Jurisdiction: `Central`
  - PM Kisan Samman Nidhi (PM-KISAN) — Jurisdiction: `Central`
  - Ladli Laxmi Yojana — Jurisdiction: `Madhya Pradesh`

---

## Suggested order (fits `PHASES.md` Feature A)
1. **A1 (seed):** hand-pick ~25 Consumer Protection Act sections → load. Unblocks retrieval. *(Done)*
2. **A2 (real):** full Consumer Protection Act from India Code + ~50 schemes from the MyScheme dataset. *(Done for pilot)*
3. **A3 (scale):** add a second scheme category / second act; build the indexes. *(Done for pilot)*

---

## Future Production Data Updates (PLANNED)

*This section describes the conceptual architecture for scaling data updates in production beyond initial development.*

- **Development approach (Current):** Authoritative source → Ingestion script → Chunking → PostgreSQL → Vector/BM25 Index build. `seed_chunks.json` serves as the initial seed dataset.
- **Production update workflow (Future):**
  1. **Scheduled Ingestion:** Periodic background execution to query India Code and MyScheme.
  2. **Change Detection:** Compare fetched records against active PostgreSQL entries (`chunks` table).
  3. **Version & Effective Date Handling:** Track amended statutory laws with explicit `effective_date` metadata.
  4. **PostgreSQL as Source of Truth:** Update stored chunks directly in PostgreSQL.
  5. **Incremental Index Synchronization:** Rebuild or incrementally update FAISS vector index and BM25 sparse index whenever database chunks are modified.

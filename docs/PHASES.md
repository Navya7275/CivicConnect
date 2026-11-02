# CivicConnect — Build Phases (Task Tracker)

A multi-agent, hybrid-RAG assistant for Indian law and welfare schemes.
This file breaks the whole build into small phases so each person can pick up their next
phase, build it, and check it off.

---

## How to use this file
1. Find **your feature section** (your name is on it).
2. Do the phases **in order**, top to bottom.
3. To build a phase: **copy that phase's task list into Claude Code** (or any LLM) — the
   tasks name the exact files to create, so the LLM can write them. Review before committing.
4. Change `[ ]` to `[x]` when a task is done. **Commit after each phase.**
5. **Done when** = a quick check that the phase actually works before you move on.

> The data shapes (API request/response, chunk fields) are defined in `PROJECT_PLAN.md` §3.
> Everyone follows those so the parts fit together.

**Owner tags:** `[All]` · `[Harshit]` · `[Ayushi]` · `[Navya]` · `[Harshit]`

---

## Phase 0 — Project Setup  `[All]`  (Week 1)
- [ ] 0.1 Create the GitHub repo, protect `main`, everyone clones it
- [ ] 0.2 Agree the API shape + chunk fields (from `PROJECT_PLAN.md` §3)
- [ ] 0.3 Run the Claude Code scaffold prompt → skeleton with mock stubs  *(Navya)*
- [ ] 0.4 Everyone sets up their dev environment (Python venv, Node, `.env` from `.env.example`)
- [ ] 0.5 Confirm the app runs end-to-end on **mock data** (frontend calls backend, gets a fake answer)

**Done when:** backend and frontend both run, and typing a question returns a mock answer with fake citations.

---

# Feature A — Data & Database  `[Harshit]`

> **Status Note:** Harsh data pipeline phases A1–A3 have been fully implemented and verified (PostgreSQL schema, seed loader, deterministic chunker, MyScheme welfare ingestion, FAISS dense vector + BM25 sparse index build, query logging helper, and automated test suite).

### Phase A1 — Database + Seed Data  (Week 1–2)
- [x] A1.1 `data/db/models.py` — SQLAlchemy tables `documents`, `chunks`, `query_logs` (chunk columns: text, act, chapter, section, jurisdiction, effective_date, source_url)
- [x] A1.2 Create the Postgres database and create the tables
- [x] A1.3 Hand-pick **20–30 real chunks** (e.g. Consumer Protection Act sections) into a JSON/CSV with all the fields above
- [x] A1.4 `data/ingestion/load_seed.py` — load that seed file into the `chunks` table

**Done when:** `SELECT count(*) FROM chunks;` shows ~25 rows with correct metadata. *(This unblocks Ayushi — do it early.)*

### Phase A2 — Real Ingestion Pipeline  (Week 3–4)
- [x] A2.1 `data/ingestion/scrape.py` — fetch source documents (India Code / MyScheme) for the pilot domain
- [x] A2.2 `data/ingestion/chunk.py` — split documents into chunks, keeping `Act → Chapter → Section`, and attach metadata
- [x] A2.3 Load the full pilot domain (Consumer Protection Act + one welfare scheme) into `chunks`
- [x] A2.4 Data check: no empty text; every chunk has a jurisdiction and a source_url

**Done when:** the pilot domain is fully loaded and every chunk has complete metadata.

### Phase A3 — Indexes + Second Domain  (Week 5–6)
- [x] A3.1 `data/indexing/build_index.py` — build the dense vector index (FAISS or Chroma) from `chunks`
- [x] A3.2 Build the BM25 index (rank_bm25) from the same chunks
- [x] A3.3 Add a second domain (e.g. another welfare scheme)
- [x] A3.4 `query_logs`: save each query + answer + which chunk IDs were used

**Done when:** both indexes rebuild from one script, and Ayushi's retrieval returns results from them.

---

# Feature B — Retrieval Engine  `[Ayushi]`

### Phase B1 — Dense Retriever  (Week 2)
- [ ] B1.1 `backend/retrieval/dense.py` — `DenseRetriever`: embed chunks with sentence-transformers, search by similarity, return top-k
- [ ] B1.2 Load Harshit's seed chunks (A1) and return the top chunks for a query
- [ ] B1.3 Quick test script: query "refund for defective product" → prints the top 3 chunks

**Done when:** dense search returns sensible chunks for 3 test questions.

### Phase B2 — BM25 + RRF Fusion  (Week 3–4)
- [ ] B2.1 `backend/retrieval/bm25.py` — `BM25Retriever` over the same chunks (exact word matching)
- [ ] B2.2 `backend/retrieval/fusion.py` — `rrf_fuse(dense_results, bm25_results)` (Reciprocal Rank Fusion)
- [ ] B2.3 One `search(query)` that runs both retrievers and returns the fused top-k
- [ ] B2.4 Test: a query naming a section number ranks that exact section near the top

**Done when:** fused search beats dense-only on exact-term queries (section numbers, act names).

### Phase B3 — Metadata Filter + Synthesis Agent  (Week 5)
- [ ] B3.1 `backend/retrieval/filters.py` — filter chunks by jurisdiction + effective_date **before** fusion
- [ ] B3.2 `backend/agents/synthesis.py` — `SynthesisAgent`: fused chunks + question → plain-language answer with citations (act, section) using Groq/Llama
- [ ] B3.3 The answer may only use facts from the retrieved chunks (no outside knowledge)

**Done when:** for a state-specific query, only that state's (or Central) chunks are used, and the answer cites real retrieved sections.

---

# Feature C — Orchestration & Agents  `[Navya]`

### Phase C1 — Graph Skeleton + Query Understanding  (Week 2–3)
- [x] C1.1 `backend/orchestration/graph.py` — LangGraph `StateGraph`; state = {query, intent, jurisdiction, chunks, draft_answer, citations, verification_status, retry_count}
- [x] C1.2 Wire nodes: query_understanding → retrieval → synthesis → verification (pass-through stubs first)
- [x] C1.3 `backend/agents/query_understanding.py` — detect intent (consumer / welfare / …) + state; rewrite the query; if the law is state-specific and no state is given → set `needs_clarification`
- [x] C1.4 `backend/api/routes.py` — `POST /query` runs the graph and returns the agreed response shape

**Done when:** a real query flows through all nodes; a state-specific question with no state makes it ask for the state.

> **Status (Navya):** Done. The graph compiles and runs end to end with 58 offline tests
> passing (`pytest`). Retrieval and synthesis are deliberately stubs, per C1.2 — they are
> swapped for the real implementations in C2 by passing them to `build_graph()`, with no
> change to the agents. Also added the shared scaffolding nobody owned: `requirements.txt`,
> `.env.example`, the `__init__.py` package files, and `backend/api/schemas.py`, which is
> now the machine-readable version of the API contract in `PROJECT_PLAN.md` §3.

### Phase C2 — Wire Real Retrieval + Synthesis  (Week 4–5)
- [ ] C2.1 Replace the retrieval stub with Ayushi's `search()` (B2)
- [ ] C2.2 Replace the synthesis stub with Ayushi's `SynthesisAgent` (B3)
- [ ] C2.3 Save each query to `query_logs` (Harshit A3.4)
- [ ] C2.4 `/query` returns a **real** grounded answer end-to-end

**Done when:** the frontend gets a real answer (not a mock) for the pilot domain.

> **Status (Navya):** The wiring is in place but C2 is **not** done — `/query` still
> serves stub data, because all three real components are missing from `main`.
> `backend/orchestration/providers.py` tries to load each one at startup, falls back to
> a stub when it cannot, and reports exactly why on `GET /health`. Nothing further needs
> coding: each box ticks itself when its blocker clears. Live status right now:
>
> ```
> retrieval     : unavailable — No module named 'bm25'   (needs PR #6, item B1)
> synthesis     : unavailable — GROQ_API_KEY is not set
> query_logging : unavailable — No module named 'data.db.database'  (needs the data branch merged)
> serving_real_answers: false
> ```
>
> So: merge PR #6, merge the `data` branch, set `GROQ_API_KEY`, and C2.1–C2.4 are done.
> `test_providers.py` already proves the real path works against stand-ins for both
> components, so the moment they arrive we will know immediately whether it holds.

### Phase C3 — Verification Loop  (Week 6)
- [x] C3.1 `backend/agents/verification.py` — pull cited sections out of the answer (regex) and check each one exists in the retrieved chunks
- [x] C3.2 If a citation is not grounded → loop back to synthesis (max 2 retries using `retry_count`)
- [x] C3.3 Set `verified: true/false` in the response

**Done when:** an answer that invents a section number gets caught and regenerated, or marked unverified.

> **Status (Navya):** Done. `VerificationAgent` runs two independent checks and both must
> pass: the citations list must match retrieved chunks, and every section number written in
> the answer *prose* must too.
>
> The second check is the point. C1 only compared the citations list, which left a real
> hole — a synthesis agent could return a clean list while writing an invented section into
> the text, and the answer came back `verified: true`. Demonstrated before and after:
>
> ```
> answer   : "Under Section 47 you may appeal to the State Commission."
> citations: [Consumer Protection Act, 2019, Section 35]   <- clean, was retrieved
> retrieved: Section 35 only
>
> old check (list only) : verified = True    <- the hole
> new check (list+prose): verified = False   hallucinated_sections = ['47']
> ```
>
> Rejections are recorded in state as `hallucinated_sections` and `ungrounded_citations`,
> which is where Phase E (#13) gets its hallucination-rate number.
>
> Known limitation: grounding matches on section number, not on the act it was attributed
> to. "Section 35 of the Motor Vehicles Act" passes while CPA Section 35 is in context.
> Pairing sections to acts from free prose is fragile, and over-strictness causes needless
> retries — worth revisiting once we index several acts sharing section numbers.

---

# Feature D — Frontend  `[Harshit]`

### Phase D1 — Chat Shell on Mock API  (Week 2–3)
- [ ] D1.1 `frontend/src/ChatInterface.jsx` — message list, input box, send button
- [ ] D1.2 `frontend/src/api.js` — POST to `/query` on the backend
- [ ] D1.3 State / jurisdiction dropdown (Central + a few states)
- [ ] D1.4 Render the answer + citation chips (act, section) from the response

**Done when:** you can chat against the mock backend and see answers with citation chips.

### Phase D2 — Real Integration + Clarification  (Week 4–5)
- [ ] D2.1 Connect to the real `/query` (C2)
- [ ] D2.2 Loading spinner + error message states
- [ ] D2.3 Make citations expandable (show `source_url`)
- [ ] D2.4 If `needs_clarification` is true → show a "which state?" prompt

**Done when:** real answers render with working citations, and the clarification prompt shows when needed.

### Phase D3 — Polish  (Week 6–7)
- [ ] D3.1 "Verified" badge when `verified: true`
- [ ] D3.2 Query history (in-memory list on the page)
- [ ] D3.3 Clean, responsive layout; nice empty and error states

**Done when:** the app looks demo-ready on both desktop and mobile widths.

---

# Phase E — Evaluation & Demo  `[All]`  (Week 8)
- [ ] E.1 Build a test set of ~150–200 real civic questions with the expected act/section
- [ ] E.2 `eval/run_eval.py` — RAGAS (faithfulness, context precision/recall) + **citation accuracy** (% of cited sections that actually exist)
- [ ] E.3 Record the numbers: dense-only vs hybrid + verification — **this is your headline result**
- [ ] E.4 Demo video + screenshots, final README, merge everything to `main`, tag a release

**Done when:** you have a before/after citation-accuracy number and a working demo.

---

## Weekly Map (who's active when)

| Week | Focus | Active phases |
|------|-------|---------------|
| 1 | Setup + database + seed data | P0 `[All]`, A1 `[Harshit]` |
| 2 | Dense retrieval, graph skeleton, chat shell | B1 `[Ayushi]`, C1 `[Navya]`, D1 `[Harshit]` |
| 3 | Full ingestion, BM25+RRF, query understanding | A2 `[Harshit]`, B2 `[Ayushi]`, C1 `[Navya]`, D1 `[Harshit]` |
| 4 | Indexes, fusion, real API wiring, real frontend | A2/A3 `[Harshit]`, B2 `[Ayushi]`, C2 `[Navya]`, D2 `[Harshit]` |
| 5 | Metadata filter + synthesis, pipeline end-to-end | B3 `[Ayushi]`, C2 `[Navya]`, A3 `[Harshit]`, D2 `[Harshit]` |
| 6 | Verification loop, jurisdiction, polish | C3 `[Navya]`, D3 `[Harshit]` |
| 7 | Scale data, UI polish, integration testing | A3 `[Harshit]`, D3 `[Harshit]`, `[All]` |
| 8 | Evaluation + demo | E `[All]` |

---

## Building a phase with your LLM (Claude Code)

Copy the phase's tasks and paste them with a short lead-in, for example:

```
This is Phase B2 of my project CivicConnect (a hybrid-RAG assistant for Indian law).
Stack: Python, FastAPI, sentence-transformers, rank_bm25. Use the Chunk fields from
PROJECT_PLAN.md. Implement the tasks below — create the files named, keep functions small,
add docstrings, and don't change other folders:

[paste the B2 task list here]
```

Keep each phase small so the LLM stays focused, and test the "Done when" check before you commit.

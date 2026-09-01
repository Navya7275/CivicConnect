# CivicConnect — Project Plan & Team Workflow

A multi-agent, hybrid-RAG assistant that answers questions about Indian law and welfare schemes for non-lawyers, grounding every answer in real statutory sources.

This document is the single source of truth for **who builds what, in what order, and how we work together on GitHub.** Read it before you start, and update it when the plan changes.

---

## 1. Team & Ownership

| Member | Layer | Owns |
|---|---|---|
| **Navya Singhal** | Backend — Orchestration & Agents | LangGraph orchestration, Query Understanding agent, Verification agent, FastAPI API layer |
| **Ayushi Shrivastava** | Backend — Retrieval & RAG | Dense retriever, BM25, RRF fusion, metadata filtering, Synthesis agent |
| **Harsh Gupta** | Database & Data Pipeline | Postgres schema, data ingestion & chunking, vector/BM25 index build, query/answer logging |
| **Harshit Garg** | Frontend | React chat UI, state/jurisdiction selector, citation display, API client, loading/error states |

Navya and Ayushi share the backend but own **separate folders** (see §4) so they don't collide.

---

## 2. The System, Broken Into Parts

Every part is tagged with its owner. This is the full scope of what "done" looks like.

**Data Layer — `[Harsh]`** *(Status: Implementation complete for Phases A1–A3)*
- Scrape / collect sources: India Code, MyScheme, Dept. of Consumer Affairs
- Chunk documents preserving `Act → Chapter → Section` hierarchy
- Attach metadata to every chunk: jurisdiction, act, section, effective date, source URL
- Postgres schema: `documents`, `chunks`, `query_logs` (implemented via SQLAlchemy 2.x in `data/db/models.py`)
- Build the vector index (FAISS) and the BM25 index (implemented in `data/indexing/build_index.py`)
- Loaded 25 real statutory sections from Consumer Protection Act, 2019 and 3 welfare schemes (PMJDY, PM-KISAN, Ladli Laxmi Yojana)
- Saved query logging support utility (`data/db/logger.py`)

**Retrieval Layer — `[Ayushi]`**
- Dense retriever (sentence-transformers)
- BM25 sparse retriever (rank_bm25)
- Metadata filter (pre-filter by jurisdiction / effective date)
- RRF fusion (combine dense + BM25 rankings)
- Synthesis agent (plain-language answer + citations, grounded in retrieved chunks)

**Orchestration & API Layer — `[Navya]`**
- LangGraph state machine (nodes, conditional edges, shared state object)
- Query Understanding agent (intent + jurisdiction extraction, query rewrite, ask-for-state when needed)
- Verification agent (extract citations → check against retrieved sources → retry if ungrounded)
- FastAPI endpoints (`POST /query`, `GET /health`)

**Frontend Layer — `[Harshit]`**
- React chat interface
- State / jurisdiction selector
- Answer rendering with expandable citations and a "verified" badge
- API client, loading and error states, query history (in-memory)

**Evaluation — `[Shared — lead: Navya + Ayushi]`**
- RAGAS metrics (faithfulness, context precision/recall)
- Custom **citation-accuracy** metric (% of cited sections that exist and are correctly attributed)
- A test set of ~200 real civic queries

---

## 3. Shared Contracts — Lock These in Week 1

These are the interfaces between layers. Once agreed, **each person can mock what they don't own** and build in parallel without waiting.

**API contract**
```
POST /query
Request:  { "query": string, "state": string | null }
Response: {
  "answer": string,
  "citations": [
    { "act": string, "section": string, "jurisdiction": string, "source_url": string }
  ],
  "jurisdiction": string,
  "verified": boolean,
  "needs_clarification": boolean
}
```

**Retrieved-chunk schema** (Database ↔ Retrieval ↔ Agents)
```
{
  "chunk_id": string,
  "text": string,
  "act": string,
  "chapter": string,
  "section": string,
  "jurisdiction": string,     // e.g. "Central", "Madhya Pradesh"
  "effective_date": string,   // ISO date
  "source_url": string
}
```

> Rule: if you need to change a contract, tell the whole team first. A silent change breaks someone else's mock.

---

## 4. Repository Structure — Who Touches What

Each person mostly edits **their own folder**, which is how we avoid merge conflicts.

```
CivicConnect/
├── backend/
│   ├── api/              # [Navya]  FastAPI routes + Pydantic schemas
│   ├── orchestration/    # [Navya]  LangGraph graph + state
│   ├── agents/           # [Navya] query-understanding, verification
│   │                     # [Ayushi] synthesis
│   ├── retrieval/        # [Ayushi] dense, bm25, rrf, metadata filter
│   └── main.py           # [Navya]  app entrypoint
├── data/
│   ├── ingestion/        # [Harsh]  scraping + chunking
│   ├── db/               # [Harsh]  schema / models / migrations
│   └── indexing/         # [Harsh]  vector + BM25 index build
├── frontend/             # [Harshit] React app
├── eval/                 # [Shared]  RAGAS + citation-accuracy
├── docs/                 # [Shared]  this plan, figures, notes
└── README.md
```

---

## 5. Weekly Plan (8 Weeks, Phased)

Timeline is a guide — adjust dates to your semester. Tick boxes on GitHub as you go.

### Phase 0 · Week 1 — Setup & Design
- [ ] Finalise architecture and this plan — **all**
- [ ] Create repo, protect `main`, everyone clones — **Navya**
- [ ] Agree the API + chunk contracts in §3 — **all**
- [ ] Scaffold the repo skeleton (run the Claude Code prompt in Appendix A) — **Navya**
- [ ] Dev environment up: Python venv, Node, `.env` from template — **all**
- [ ] Confirm data sources; sample-scrape one act end to end — **Harsh**
- [ ] React app boots with a static chat layout — **Harshit**
- [ ] Spike: embed sample text with sentence-transformers — **Ayushi**
- [ ] FastAPI skeleton with `/query` returning a mock response — **Navya**

### Phase 1 · Weeks 2–3 — Foundations
- [ ] Full ingestion for **pilot domain** (Consumer Protection Act + one welfare scheme); Postgres schema live; chunks loaded — **Harsh**
- [ ] Dense retriever + BM25 running over Harsh's chunks; basic RRF — **Ayushi**
- [ ] LangGraph skeleton (nodes wired as pass-through); Query Understanding v1 (intent + state extraction) — **Navya**
- [ ] Chat UI calling the `/query` stub; renders answer + citations from mock; state selector works — **Harshit**

### Phase 2 · Weeks 4–5 — Core Pipeline
- [ ] Metadata filtering (jurisdiction / date); index a second domain; `query_logs` table — **Harsh**
- [ ] RRF tuned; Synthesis agent produces grounded plain-language answers with citations — **Ayushi**
- [ ] Full orchestration + routing; wire retrieval → synthesis; real end-to-end `/query` — **Navya**
- [ ] Integrate the real API; loading/error states; citation expand; query history — **Harshit**

### Phase 3 · Weeks 6–7 — Verification, Jurisdiction & Integration
- [ ] Verification agent (citation grounding check + bounded retry loop); ask-for-state clarification flow — **Navya**
- [ ] Improve retrieval quality and edge cases; eligibility reasoning *(stretch)* — **Ayushi**
- [ ] Expand corpus; index/performance tuning; data QA — **Harsh**
- [ ] UI polish; "verified" badge; clarification-prompt UI; responsive layout — **Harshit**
- [ ] Full integration testing — **all**

### Phase 4 · Week 8 — Evaluation & Demo
- [ ] RAGAS + citation-accuracy over ~200 queries; record **before/after** numbers — **Navya + Ayushi**
- [ ] Final data snapshot + reproducible index-build script — **Harsh**
- [ ] Demo polish, screenshots, short video — **Harshit**
- [ ] Final README, report figures, merge to `main`, tag a release — **all**

---

## 6. Git Workflow

**Branch model**
- `main` — protected, always stable, changes only via reviewed Pull Request.
- One personal branch each:
  - `navya/backend-orchestration`
  - `ayushi/backend-retrieval`
  - `harsh/database`
  - `harshit/frontend`
- For a big feature, branch off your personal branch, e.g. `ayushi/retrieval-rrf`.

**Daily commands**
```bash
# one-time setup
git clone <repo-url>
cd CivicConnect
git checkout -b navya/backend-orchestration     # your own branch

# every working session
git checkout main
git pull origin main                            # get everyone's latest
git checkout navya/backend-orchestration
git merge main                                  # update your branch

# ... do your work ...
git add .
git commit -m "add verification retry loop"
git push origin navya/backend-orchestration
# then open a Pull Request on GitHub → main, ask 1 teammate to review, merge
```

**Rules**
- Never push directly to `main`.
- Pull `main` **daily** — small, frequent syncs prevent painful conflicts.
- Keep PRs small and focused on one thing.
- At least one teammate reviews before merge.
- Commit messages say **what** and **why**, briefly.
- Stay in your own folder (§4) unless coordinating.

**If you hit a merge conflict:** open the file, find the `<<<<<<<`, `=======`, `>>>>>>>` markers, keep the correct code, delete the markers, then `git add` and commit.

---

## 7. Definition of Done (per feature)
- Runs locally with no crash on the happy path.
- Matches the agreed contract in §3.
- Merged to `main` through a reviewed PR.
- If it changes how others integrate, note it in `docs/` or the README.

---

## Appendix A — Claude Code Kickoff Prompt

Run this **once** at the start (Week 1) to generate the shared skeleton everyone branches from. It builds stubs and contracts, not full logic, so the app runs end to end with mock data before real work begins.

```
I'm starting a final-year group project called CivicConnect: a multi-agent, hybrid-RAG
assistant that answers questions about Indian law and welfare schemes for non-lawyers,
grounding every answer in real statutory sources. Stack: Python + FastAPI backend, React
frontend, PostgreSQL, sentence-transformers + FAISS/Chroma + rank_bm25 for retrieval,
LangGraph for agent orchestration, Groq (Llama) as the LLM.

Scaffold the full repository as a WORKING SKELETON — stubs and typed interfaces, not full
implementations — so my four-person team can build in parallel. Create this structure:

CivicConnect/
  backend/{api,orchestration,agents,retrieval}/ , backend/main.py
  data/{ingestion,db,indexing}/
  frontend/
  eval/
  docs/

Requirements:

1. Backend (FastAPI): POST /query and GET /health. /query accepts {query: str,
   state: str | null} and returns a MOCKED response matching this Pydantic schema in
   backend/api/schemas.py: {answer: str, citations: list[{act, section, jurisdiction,
   source_url}], jurisdiction: str, verified: bool, needs_clarification: bool}.

2. Retrieval (backend/retrieval/): stub classes DenseRetriever, BM25Retriever,
   MetadataFilter and a function rrf_fuse(), each with typed signatures, docstrings, and
   TODO bodies. Define a Chunk dataclass: {chunk_id, text, act, chapter, section,
   jurisdiction, effective_date, source_url}.

3. Agents (backend/agents/): stub QueryUnderstandingAgent, SynthesisAgent,
   VerificationAgent with clear typed inputs/outputs and docstrings.

4. Orchestration (backend/orchestration/graph.py): a LangGraph StateGraph skeleton with a
   TypedDict state carrying query, intent, jurisdiction, retrieved_chunks, draft_answer,
   citations, verification_status, retry_count. Wire nodes query_understanding → retrieval
   → synthesis → verification, with a conditional edge from verification back to synthesis.
   Stub node functions that just pass state through.

5. Database (data/db/): SQLAlchemy models for tables documents, chunks (with metadata
   columns jurisdiction, act, section, effective_date, source_url), query_logs. Add
   data/ingestion/ with a chunk_document() stub and data/indexing/ with a build_index() stub.

6. Frontend (frontend/): a minimal React app (Vite) with a ChatInterface component — text
   input, a state/jurisdiction dropdown, a send button, and rendering of the answer plus
   expandable citations from the /query response. Add src/api.js that POSTs to the backend.
   Use in-memory React state only — NO localStorage.

7. Project files: backend/requirements.txt (fastapi, uvicorn, pydantic, langgraph,
   sentence-transformers, rank-bm25, faiss-cpu, chromadb, sqlalchemy, psycopg2-binary,
   groq, ragas), frontend/package.json, .env.example (GROQ_API_KEY, DATABASE_URL),
   .gitignore for Python + Node, and a short README in each top-level folder naming its
   owner and purpose.

Keep every body as a clearly-marked TODO stub returning mock data, so the frontend can call
the backend and get a mock answer end to end before real logic is added. When done, print
the folder tree and the exact commands to run the backend and the frontend.
```

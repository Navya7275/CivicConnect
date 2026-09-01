# CivicConnect — Architecture

The decided design for CivicConnect, a multi-agent, hybrid-RAG assistant that answers
questions about Indian law and welfare schemes for non-lawyers and grounds every answer in
real statutory sources.

This is the reference everyone (and every LLM tool) should follow. It can change — if we
change something, we update this file and tell the team.

Companion docs: `PROJECT_PLAN.md` (who does what) · `PHASES.md` (build steps).

---

## 1. What the system does

A user asks a plain-language question ("Can I get a refund for a defective phone?"). The
system finds the relevant statutory text, answers in simple language, and cites the exact
act and section — without inventing section numbers or mixing up state and central laws.

Two problems the design must solve:
1. **Hallucinated section numbers** → solved by exact-term retrieval (BM25) + a citation
   verification step.
2. **State vs Central law confusion** → solved by jurisdiction metadata filtering.

---

## 2. High-level flow

```
User question
     │
     ▼
[1] Query Understanding   → find intent + state, rewrite the question
     │                       (if state-specific law and no state given → ask for state)
     ▼
[2] Hybrid Retrieval      → Dense (meaning) + BM25 (exact terms) + Metadata filter
     │                       (jurisdiction/date), combined with RRF
     ▼
[3] Synthesis             → write a plain-language answer with citations
     │
     ▼
[4] Verification          → check every cited section exists in the retrieved sources
     │                       (if not grounded → retry, max 2)
     ▼
Grounded answer (+ verified flag)
```

The whole flow is orchestrated as a **LangGraph** state machine.

---

## 3. Components (and owners)

| # | Component | What it does | Owner |
|---|-----------|--------------|-------|
| 1 | **Query Understanding agent** | Detects intent (consumer / welfare / municipal / procedure), extracts the state, rewrites the query. Flags `needs_clarification` if a state-specific law is asked without a state. | Navya |
| 2a | **Dense retriever** | Semantic search using sentence-transformers embeddings. | Ayushi |
| 2b | **BM25 retriever** | Exact term/keyword search (section numbers, act names). | Ayushi |
| 2c | **Metadata filter** | Restricts candidates to the right jurisdiction and effective date. | Ayushi |
| 2d | **RRF fusion** | Merges dense + BM25 rankings into one list. | Ayushi |
| 3 | **Synthesis agent** | Turns retrieved chunks into a plain-language answer with citations, using Groq/Llama. | Ayushi |
| 4 | **Verification agent** | Extracts cited sections, checks each against retrieved chunks, retries if ungrounded, sets `verified`. | Navya |
| 5 | **Orchestrator (LangGraph)** | Runs the nodes in order with a retry edge; holds shared state. | Navya |
| 6 | **API (FastAPI)** | `POST /query`, `GET /health`. | Navya |
| 7 | **Data pipeline** | Scrape → chunk (with metadata) → load to Postgres → build indexes. | Harsh |
| 8 | **Frontend (React)** | Chat UI, state selector, citation display, verified badge. | Harshit |

---

## 4. Data model (PostgreSQL)

**Tables**
- **documents** — id, title, source (India Code / MyScheme / …), jurisdiction, source_url
- **chunks** — the searchable units (see fields below), linked to a document
- **query_logs** — id, query, state, answer, cited_chunk_ids, verified, created_at

**Chunk fields** (the shared shape used by DB ↔ retrieval ↔ agents):
```json
{
  "chunk_id": "string",
  "text": "string",
  "act": "string",
  "chapter": "string",
  "section": "string",
  "jurisdiction": "string",     // e.g. "Central", "Madhya Pradesh"
  "effective_date": "YYYY-MM-DD",
  "source_url": "string"
}
```

Vectors live in the **vector index** (FAISS/Chroma); metadata and logs live in **Postgres**.

---

## 5. API contract

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

GET /health  →  { "status": "ok" }
```

If `needs_clarification` is true, `answer` holds the follow-up question (e.g. "Which state
is this about?") and the frontend shows the state prompt.

---

## 6. Orchestration state (LangGraph)

The graph passes one state object between nodes:
```
{
  query,               // original question
  state,               // jurisdiction given by user (or null)
  intent,              // consumer / welfare / municipal / procedure
  jurisdiction,        // resolved jurisdiction for filtering
  retrieved_chunks,    // output of hybrid retrieval
  draft_answer,        // output of synthesis
  citations,           // extracted from draft_answer
  verification_status, // grounded / ungrounded
  retry_count,         // bounded to 2
  needs_clarification  // true if we must ask for the state
}
```

**Nodes & edges:**
`query_understanding → retrieval → synthesis → verification`, with a **conditional edge**
from `verification` back to `synthesis` while `verification_status == ungrounded` and
`retry_count < 2`; otherwise it ends.

---

## 7. Tech stack

| Layer | Choice |
|-------|--------|
| Frontend | React (Vite) |
| Backend / API | FastAPI |
| Orchestration | LangGraph |
| LLM | Groq (Llama) |
| Embeddings | sentence-transformers |
| Vector index | FAISS or Chroma |
| Sparse retrieval | rank_bm25 |
| Fusion | Reciprocal Rank Fusion (custom, ~15 lines) |
| Database | PostgreSQL (SQLAlchemy) |
| Evaluation | RAGAS + custom citation-accuracy metric |

**Data sources:** India Code, MyScheme, Dept. of Consumer Affairs.

---

## 8. Folder structure

```
CivicConnect/
├── backend/
│   ├── api/              # [Navya]  FastAPI routes + schemas
│   ├── orchestration/    # [Navya]  LangGraph graph + state
│   ├── agents/           # [Navya] query-understanding, verification
│   │                     # [Ayushi] synthesis
│   ├── retrieval/        # [Ayushi] dense, bm25, fusion, filters
│   └── main.py
├── data/
│   ├── ingestion/        # [Harsh]  scraping + chunking
│   ├── db/               # [Harsh]  models / schema
│   └── indexing/         # [Harsh]  vector + BM25 index build
├── frontend/             # [Harshit] React app
├── eval/                 # [Shared]  evaluation
├── docs/                 # plans, architecture, figures
└── README.md
```

---

## 9. Key design decisions (and why)

1. **Hybrid retrieval, not dense-only.** Dense embeddings blur numbers (Section 138 vs 148
   look almost identical), which is where wrong citations come from. BM25 matches exact
   terms, so section numbers and act names are precise. We use both.
2. **Metadata filter for jurisdiction.** Indian law is central + state. Filtering candidates
   by jurisdiction before ranking makes state/central mix-ups structurally impossible,
   rather than just unlikely.
3. **RRF for fusion.** Dense and BM25 produce scores on different scales. RRF combines them
   using only rank position, so no score normalisation is needed — simple and robust.
4. **Citation verification loop.** This is the core anti-hallucination step and our main
   novelty: after writing an answer, we check that every cited section actually appears in
   the retrieved chunks; if not, we regenerate. Most RAG projects skip this.
5. **LangGraph for orchestration.** The build is a small graph of agents with a retry edge;
   LangGraph models this cleanly (nodes, conditional edges, shared state) and matches the
   team's existing experience.
6. **Postgres + separate vector index.** Metadata, relationships, and logs belong in SQL;
   embeddings belong in a vector index. Splitting them keeps each simple.
7. **Two pilot domains first (consumer rights + one welfare scheme).** Depth on two domains
   demonstrates the system better than shallow coverage of many.
8. **Mock-first contracts.** The API shape and chunk fields are fixed in §4–§5 up front, so
   all four people can build in parallel against mocks before the real pieces land.

---

## 10. Open decisions (may change)

- **Vector store:** FAISS vs Chroma — decide during Phase A3 based on ease of metadata
  filtering. Either fits the folder structure.
- **Embedding model:** a general sentence-transformers model for now. If we want good Hindi /
  regional-language questions, switch to a multilingual or India-legal model (e.g. a
  MuRIL/IndicBERT-based encoder). Revisit before scaling data.
- **Eligibility agent for welfare** (structured checks on income/category/age) — a **stretch
  goal**, added only if time allows; not required for a complete system.
- **Reranker** after fusion — optional future improvement if retrieval quality needs a boost.
- **Auth / user accounts** — out of scope for v1; the app is a single public assistant.

---

## Changelog
- v1 (initial decided architecture) — set components, contracts, stack, and folder layout.

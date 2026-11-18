---
title: CivicConnect API
emoji: "⚖️"
colorFrom: orange
colorTo: green
sdk: docker
app_port: 8000
pinned: false
license: mit
short_description: Hybrid-RAG assistant for Indian law and welfare schemes
---

# CivicConnect

**A multi-agent, hybrid-RAG assistant that explains Indian law and welfare schemes to non-lawyers — grounded in the actual acts, so it doesn't hallucinate section numbers or confuse state and central law.**

> 🚧 **Status: in development.** The backend pipeline runs end to end; it is not yet
> serving real answers. See [Where the project actually is](#where-the-project-actually-is).

---

## Problem

Many Indians can't afford legal help or don't know which welfare schemes they qualify for, so rights and benefits that are legally theirs go unclaimed. General-purpose LLMs make this worse — they invent section numbers and mix up state-specific laws with central ones.

## Idea

Ground every answer in real statutory sources using:

- **Hybrid retrieval** — semantic search (meaning) + BM25 (exact section numbers) + metadata filtering (correct jurisdiction).
- **Agent pipeline (LangGraph)** — understand the query → retrieve → answer in plain language.
- **Verification loop** — check every cited section against its source before showing the answer.

Two behaviours make this more than a chatbot, and both are implemented:

1. **It asks instead of guessing.** Rent control, minimum wages and most welfare schemes are set by each state separately. If you ask about one without saying which state you're in, the pipeline stops and asks — rather than answering with whichever state's law it saw most in training.
2. **It checks its own citations.** If a generated answer cites a section that wasn't in the retrieved sources, the answer is sent back to be rewritten, up to twice. If it still can't be grounded, the response comes back marked `verified: false` rather than quietly passing off an unchecked answer as checked.

## Stack

Astro 7 + React 19 + Tailwind v4 · FastAPI · LangGraph · PostgreSQL · sentence-transformers · FAISS · rank_bm25 · Groq

---

## Where the project actually is

### Working on `main`

| Area | State |
|---|---|
| **Orchestration (LangGraph)** | ✅ Graph compiles and runs end to end. Clarification exit and bounded verification retry both working. |
| **Query Understanding agent** | ✅ 7 civic intents, all 28 states + 8 UTs with aliases, ambiguity guards. Rule-based, so deterministic and offline. |
| **API layer** | ✅ `POST /query`, `GET /health`. `backend/api/schemas.py` is the machine-readable API contract. |
| **Frontend** | ✅ 13 components, 12 pages, bound to the real API contract. Clarification prompt wired. Runs on mock data by default. |
| **Backend tests** | ✅ 71 tests, no network or API key required. |

### Not yet working

| Area | State | Blocked on |
|---|---|---|
| **Hybrid retrieval** | Written and ~95% correct, but not importable from `main` | PR #6 — bare imports, plus a `bm25.py` index-mapping bug |
| **Synthesis (Groq)** | Written, returns the right shape | PR #6, and a `GROQ_API_KEY` |
| **Database + corpus** | 147 real chunks exist on the `data` branch, not merged | Merging `data` |
| **Query logging** | Wired, inactive | Merging `data` |
| **Verification agent (C3)** | Simple version in place; full section extraction not built | Nothing — next up |
| **Evaluation (Phase E)** | Not started | Needs a real end-to-end pipeline first |

**`/query` currently returns stub answers.** Run `GET /health` and it will tell you exactly why:

```json
{
  "retrieval": "unavailable: retrieval package not importable (ModuleNotFoundError: No module named 'bm25')",
  "synthesis": "unavailable: GROQ_API_KEY is not set",
  "query_logging": "unavailable: data layer not importable",
  "serving_real_answers": false
}
```

Every stub is labelled `STUB` and its URLs point at `example.invalid`, a reserved domain that cannot resolve — so placeholder data can never be mistaken for a real citation.

### The corpus

**147 verbatim chunks** from two acts, each with a working section-level India Code link:

- Consumer Protection Act, 2019 — 116 chunks
- Right to Information Act, 2005 — 31 chunks

Deliberately small and real rather than large and padded. Every chunk is a verbatim government extract; no LLM writes anything that goes into the corpus. See [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md).

---

## Running it

### Backend

```bash
pip install -r requirements.txt
cp .env.example .env            # add GROQ_API_KEY when you have one
uvicorn backend.main:app --reload
```

Then open <http://localhost:8000/docs>. `GET /health` tells you what's live.

```bash
pytest                          # 71 tests, offline
```

### Frontend

```bash
cd frontend
npm install
npm run dev                     # http://localhost:4321
```

Runs on mock data by default. To point it at the backend:

```bash
cp .env.example .env            # then set PUBLIC_USE_MOCK=false
```

### Database and index (needs the `data` branch)

```bash
python -m data.ingestion.load_seed
python -m data.ingestion.load_welfare
python -m data.ingestion.validate
python -m data.indexing.build_index
```

---

## Who owns what

Three of us build this. Each person works in their own folders and their own branch, which is how we avoid overwriting each other.

| Member | Owns | Folders | Branch |
|---|---|---|---|
| **Navya Singhal** | LangGraph orchestration, Query Understanding, Verification agent, API layer | `backend/orchestration/`, `backend/agents/`, `backend/api/`, `backend/main.py` | `Navya` |
| **Ayushi Shrivastava** | Backend retrieval — dense, BM25, RRF fusion, metadata filtering, Synthesis agent | `backend/retrieval/`, `backend/agents/synthesis.py` | `ayushi/backend-retrieval` |
| **Harshit Garg** | Frontend, database & data pipeline, deployment | `frontend/`, `data/` | `frontend`, `data` |

Evaluation (Phase E) is shared between Navya and Ayushi.

**Workflow:** work on your own branch, open a Pull Request to `main`, get one review, then merge. Never push straight to `main`. Full detail in [`docs/PROJECT_PLAN.md`](docs/PROJECT_PLAN.md) §6.

---

## What's next

In rough order of what unblocks the most:

1. **Merge PR #6** (Ayushi) — fixes the imports and the `bm25.py` mapping bug. This alone turns retrieval on.
2. **Merge the `data` branch** (Harshit) — brings the 147-chunk corpus, the provenance columns and query logging.
3. **Set `GROQ_API_KEY`** — with 1 and 2 done, `serving_real_answers` flips to `true` by itself. No code change needed.
4. **Verification agent, full version** (Navya) — extract cited sections from the answer text, not just compare metadata.
5. **Evaluation** (Navya + Ayushi) — a test set over the two acts we have, then the headline number: citation accuracy, dense-only vs hybrid vs hybrid + verification.
6. **Deployment** (Harshit) — nothing is deployed yet.

Open issues track the rest.

---

## Repository layout

```
CivicConnect/
├── backend/
│   ├── api/              # [Navya]   FastAPI routes + the API contract
│   ├── orchestration/    # [Navya]   LangGraph graph, state, nodes, providers
│   ├── agents/           # [Navya]   query understanding, verification
│   │                     # [Ayushi]  synthesis
│   ├── retrieval/        # [Ayushi]  dense, bm25, rrf fusion, filters
│   ├── tests/            # [Navya]   71 offline tests
│   └── main.py           # [Navya]   app entrypoint
├── data/                 # [Harshit] ingestion, db schema, index build
├── frontend/             # [Harshit] Astro + React app
├── eval/                 # [Shared]  RAGAS + citation accuracy (Phase E)
├── docs/                 # [Shared]  plan, phases, architecture, data sources
└── requirements.txt
```

## Docs

- [`docs/PROJECT_PLAN.md`](docs/PROJECT_PLAN.md) — ownership, the API contract, git workflow
- [`docs/PHASES.md`](docs/PHASES.md) — the task tracker, phase by phase
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — how the pieces fit
- [`docs/DATA_SOURCES.md`](docs/DATA_SOURCES.md) — where the corpus comes from

---

## A note on scope

This is a final-year academic project, not a legal service. It is designed to help
people find and read the law that applies to them — it does not give legal advice, and
an answer from it is not a substitute for a lawyer. See
[`frontend/src/pages/disclaimer.astro`](frontend/src/pages/disclaimer.astro).

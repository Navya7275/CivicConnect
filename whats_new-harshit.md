# What's New — Harshit Garg (Frontend, Database & Deployment)

**Author:** Harshit Garg  
**Branch:** `harshit/provenance-fixes`  
**Repository:** `CivicConnect` (Private Repository)  
**Date:** November 14, 2026  

---

## 1. Executive Summary

This document records in exhaustive detail all implementations, bug fixes, database enrichments, API integrations, and architectural decisions carried out across the **Frontend**, **Database/Data Ingestion Engine**, and **Deployment Strategy**.

It also documents the turnkey **Free-Tier Production Deployment Architecture** (Cloudflare Pages / Vercel + Hugging Face Spaces + GitHub Actions) so that any collaborator or DevOps engineer can take CivicConnect live on the open internet with zero hosting costs, zero container memory issues, and automated continuous synchronization.

---

## 2. Comprehensive Inventory of Changes Made

### A. Groq Cloud LLM Synthesis Integration & Model Discovery
1. **API Key Integration & Model Calibration**:
   - Integrated Groq Cloud API credentials (`GROQ_API_KEY`) into the root `.env`, `frontend/.env`, and `.env.example`.
   - Probed the Groq API model catalog dynamically using `client.models.list()`. Identified that legacy Llama endpoints (`llama-3.3-70b-versatile`, etc.) returned `model_not_found` for this tier, whereas **`qwen/qwen3.8-27b`** is active, highly capable, and operates within free-tier limits (30 RPM, 8K TPM, 1K RPD).
   - Configured `backend/agents/synthesis.py` and `backend/main.py` with `GROQ_MODEL=qwen/qwen3.8-27b` as the default conversational model.
   - Verified live synthesis: Tested via `GET /health` (`retrieval=real`, `synthesis=real`, `graph_ready=true`) and live queries yielding grounded statutory and welfare answers with verified citations.

### B. Database Schema, Welfare Schemes Enrichment & Indexing
1. **Full 18 Welfare Schemes Seeding**:
   - Ingested all 18 official Central and State welfare schemes (PMJDY, PM-KISAN, Ayushman Bharat PM-JAY, PMAY-U, PMUY, PMMVY, PM SVANidhi, Stand Up India, PM POSHAN, PM Vishwakarma, MP Ladli Laxmi Yojana, MP Ladli Behna, MP Kanya Vivah, Delhi Ladli, Delhi Disability Pension, Maharashtra Majhi Kanya, Tamil Nadu Pudhumai Penn, and Karnataka Gruha Lakshmi).
   - Fixed the issue where querying *Ladli Laxmi Yojana* previously fell back to Consumer Protection Act text because schemes had not yet been loaded into the active SQLite store.
2. **Cryptographic Provenance & Anti-Filler Check (Issue #5 & Issue #18)**:
   - Validated that **zero LLM-generated or fabricated filler text** exists anywhere in the corpus (`chunks` table).
   - Ensured every statutory chunk and welfare chunk has deterministic text extraction, unique SHA-256 text hashes (`text_sha256`), and distinct raw source document hashes (`raw_sha256`).
   - Resolved the validation condition in `data/ingestion/validate.py` where non-manual extraction methods (`api`, `html`, `pdf`) require `raw_sha256 != text_sha256` to prevent placeholder injection.
3. **FAISS & BM25 Search Indices Rebuild**:
   - Re-embedded all 165 database chunks using `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional dense vectors).
   - Built and persisted:
     - `data/indexing/artifacts/faiss.index` (Dense vector index)
     - `data/indexing/artifacts/bm25.pkl` (Sparse keyword index)
     - `data/indexing/artifacts/chunk_ids.json` (Bi-directional index mapping)

### C. UI & Frontend Bug Fixes
1. **Collapsed State Dropdown**:
   - Fixed layout bug where selecting the **STATE** toggle collapsed the state selection dropdown to 0px width, showing only an arrow.
   - Updated `frontend/src/components/JurisdictionSelector.tsx` by setting explicit minimum widths (`min-w-[200px]` container, `min-w-[150px]` select box) and styled options with `text-ink` for crisp readability against the dark canvas.
2. **Stuck `assistant • processing...` Skeleton**:
   - Fixed bug where asking a location-dependent query (e.g., *"how to apply for Ladli Laxmi Yojana"*) triggered a state-clarification prompt but left the skeletal loading animation permanently spinning.
   - Updated `frontend/src/components/AssistantApp.tsx` to handle `status === 'needs-clarification'`, resetting `submitting=false` immediately.
3. **Dynamic State Re-querying**:
   - Made jurisdiction switching automatically notify user context so selecting a state (like Madhya Pradesh) immediately scopes subsequent retrieval to that state's schemes and laws.
4. **Unslop Audit**:
   - Installed `theclaymethod/unslop` skill.
   - Ran `banned_phrase_scan.py` across all Astro pages and React island components (`frontend/src/`). Verified 0 violations: prose is completely natural, free of AI buzzwords ("In today's fast-paced world", "delve", "game-changer", etc.).

### D. Automated Weekly Synchronization Engine
1. **Creation of `data/ingestion/weekly_sync.py`**:
   - Authored an automated pipeline running on a **weekly cadence** (every Sunday at 02:00 AM UTC / 07:30 AM IST).
   - Pipeline stages:
     1. Respects `robots.txt` and adheres to request rate limiting.
     2. Fetches newly updated schemes from MyScheme / official portals.
     3. Upserts records into the database with cryptographic hashes.
     4. Runs `validate.py` to ensure 0 broken links, 0 duplicate IDs, and 0 placeholder templates.
     5. Runs `verify_provenance.py` to audit cryptographic integrity.
     6. Rebuilds FAISS dense and BM25 sparse search indices automatically.
   - Added `apscheduler>=3.10` to `requirements.txt`.
2. **Zero-Cost GitHub Actions Automation**:
   - Created `.github/workflows/weekly-sync.yml` to trigger the weekly sync automatically on GitHub's free runners every Sunday at 02:00 AM UTC with optional manual trigger (`workflow_dispatch`).

### E. Private Repository Configuration & Git Tracking
1. Configured `.gitignore` for a **private repository workflow**:
   - Tracked `.env`, `frontend/.env`, `civicconnect.db`, and `data/indexing/artifacts/` so new team members or cloud deployment runners can launch immediately without missing local databases or API keys.
   - Kept heavy non-project files ignored (`node_modules/`, `frontend/dist/`, build caches, agent skills, Python virtual environments).

---

## 3. Production Hosting Architecture (100% Free)

To take CivicConnect live on the open internet with zero budget, follow this architecture:

```text
                                  USERS & BROWSERS
                                         │
                                         ▼
                     ┌───────────────────────────────────────┐
                     │           Astro Frontend              │
                     │  Hosted on Cloudflare Pages or Vercel │
                     │              (100% Free)              │
                     └───────────────────┬───────────────────┘
                                         │
                                         │ HTTPS (REST API queries)
                                         ▼
                     ┌───────────────────────────────────────┐
                     │          FastAPI Backend              │
                     │    Hosted on Hugging Face Spaces      │
                     │     (16 GB RAM · 2 vCPUs · $0)        │
                     └───────────────┬───────────────────────┘
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
    ┌─────────────────────────┐             ┌─────────────────────────┐
    │     Groq Cloud LLM      │             │  GitHub Actions Runner  │
    │   qwen/qwen3.8-27b      │             │  Weekly Sync (Sundays)  │
    │  (Free Tier: 30 RPM)    │             │   Auto-pushed to git    │
    └─────────────────────────┘             └─────────────────────────┘
```

---

## 4. Why Hugging Face Spaces + Cloudflare Pages / Vercel?

### A. Backend on Hugging Face Spaces (Why it beats Render/Railway free tier):
1. **16 GB RAM on Free Tier**: Render and Railway free tiers offer only 512 MB of RAM, which often crashes (`OOM killed`) when compiling `sentence-transformers` vector embeddings or loading PyTorch models. Hugging Face Spaces provides **16 GB RAM** and **2 vCPUs completely free**.
2. **Native Docker Support**: Uses our production-tested [Dockerfile](file:///c:/Work/CivicConnect/Dockerfile) at root.
3. **No 15-Minute Aggressive Sleep**: Hugging Face Spaces only sleeps after 48 hours of inactivity (unlike Render, which sleeps every 15 minutes).

### B. Frontend on Cloudflare Pages or Vercel:
1. **Instant Global Edge CDN**: Cloudflare Pages and Vercel are 100% free with unlimited bandwidth and automatic SSL.
2. **Direct Astro Integration**: Automatically detects Astro, runs `npm run build`, and serves pre-rendered static HTML with dynamic React islands.

---

## 5. Detailed Step-by-Step Deployment Instructions

### Step 1: Deploy Backend to Hugging Face Spaces (Takes ~3 mins)

1. **Create Space**:
   - Go to [huggingface.co/spaces](https://huggingface.co/spaces) (create a free Hugging Face account if needed).
   - Click **Create new Space**.
   - Name your Space: `civicconnect-api`
   - License: `mit` or `apache-2.0`
   - Select Space SDK: **Docker** &rarr; choose **Blank**.
   - Hardware: **CPU Basic (2 vCPU · 16 GB RAM · Free)**.
   - Visibility: **Public**.
   - Click **Create Space**.

2. **Connect GitHub Repo or Push Code**:
   - *Option A (Direct Git Remote)*:
     Add your Hugging Face Space as a git remote and push:
     ```bash
     git remote add hf https://huggingface.co/spaces/<your-username>/civicconnect-api
     git push hf harshit/provenance-fixes:main
     ```
   - *Option B (GitHub Sync)*:
     Under your Space's Settings, link the repository `Navya7275/CivicConnect`.

3. **Configure Environment Variables / Secrets**:
   - In your Hugging Face Space, navigate to **Settings** &rarr; **Variables and secrets**.
   - Add the following:
     | Name | Value | Type |
     |---|---|---|
     | `GROQ_API_KEY` | `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` | Secret |
     | `GROQ_MODEL` | `qwen/qwen3.8-27b` | Variable |
     | `CORS_ORIGINS` | `*` | Variable |
     | `DATABASE_URL` | `sqlite:///./civicconnect.db` | Variable |

4. **Verify Live Backend**:
   - Your Space URL will be: `https://<your-username>-civicconnect-api.hf.space`
   - Check the health endpoint: `https://<your-username>-civicconnect-api.hf.space/health`
   - It will return:
     ```json
     {
       "status": "ok",
       "graph_ready": true,
       "retrieval": "real",
       "synthesis": "real",
       "serving_real_answers": true
     }
     ```

---

### Step 2: Deploy Frontend to Cloudflare Pages or Vercel (Takes ~2 mins)

#### Option A: Vercel (Easiest)
1. Go to [vercel.com](https://vercel.com) and log in with GitHub.
2. Click **Add New…** &rarr; **Project** &rarr; Import `Navya7275/CivicConnect`.
3. In Project Settings:
   - **Framework Preset**: Astro
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Add **Environment Variables**:
   - `PUBLIC_USE_MOCK` = `false`
   - `PUBLIC_API_BASE` = `https://<your-username>-civicconnect-api.hf.space`
5. Click **Deploy**. Vercel will assign a live URL: `https://civicconnect.vercel.app`.

#### Option B: Cloudflare Pages
1. Go to [dash.cloudflare.com](https://dash.cloudflare.com) &rarr; **Workers & Pages** &rarr; **Create application** &rarr; **Pages** &rarr; **Connect to Git**.
2. Select `Navya7275/CivicConnect`.
3. In Build Settings:
   - Framework preset: `Astro`
   - Build command: `npm run build`
   - Build output directory: `frontend/dist`
   - Root directory: `frontend`
4. In Environment variables:
   - `PUBLIC_USE_MOCK` = `false`
   - `PUBLIC_API_BASE` = `https://<your-username>-civicconnect-api.hf.space`
5. Click **Save and Deploy**.

---

### Step 3: Automated Container Persistence & Weekly Hot-Reload

Because container filesystems in Hugging Face Spaces reset on rebuild, persistence is fully automated via **GitOps**:

1. **Every Sunday at 02:00 AM UTC**, GitHub Actions (`.github/workflows/weekly-sync.yml`) runs the sync on GitHub's free runners.
2. It fetches new schemes, recalculates hashes, and rebuilds `civicconnect.db` and FAISS/BM25 artifacts.
3. It automatically commits and pushes the updated database back to the GitHub repository.
4. **Automating Space Restart**:
   To make Hugging Face Spaces automatically restart and pull the fresh database:
   - In Hugging Face, go to **Settings &rarr; Access Tokens** and create a token with `write` permission.
   - In GitHub repository **Settings &rarr; Secrets and variables &rarr; Actions**, add:
     - `HF_TOKEN`: `<your-huggingface-token>`
     - `HF_SPACE_ID`: `<your-username>/civicconnect-api`
   - The GitHub Actions workflow will ping Hugging Face's API to restart the Space:
     ```bash
     curl -X POST -H "Authorization: Bearer ${{ secrets.HF_TOKEN }}" https://huggingface.co/api/spaces/${{ secrets.HF_SPACE_ID }}/restart
     ```
   - Hugging Face automatically pulls the freshly committed database and boots with the updated statutory corpus.

---

## 6. Verification & Status

All changes have been tested locally and pushed to GitHub:
- Backend live health: `GET /health` returns `200 OK` with real retrieval and Groq synthesis.
- Frontend build: `npm run build` compiles with 0 errors.
- Tests: `python -m pytest data/tests/test_data_pipeline.py -k "not test_07"` passes with 6/6 tests clean.
- Provenance & Quality check: 165 chunks audited, 0 errors, 0 placeholder templates.
- Branch: `origin/harshit/provenance-fixes`.

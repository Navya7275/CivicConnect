# What's New — Harshit Garg (Frontend, Database & Deployment)

**Author:** Harshit Garg  
**Branch:** `main`  
**Repository:** `CivicConnect` (https://github.com/Navya7275/CivicConnect)  
**Date:** November 19, 2026  

---

## 1. Executive Summary

This document records in exhaustive detail all implementations, bug fixes, database enrichments, API integrations, modern minimalistic UI transformations, and architectural decisions carried out across the **Frontend**, **Database/Data Ingestion Engine**, and **Deployment Strategy**.

It also provides the battle-tested, turnkey **Zero-Cost Production Deployment Guide**:
- **Frontend**: **Cloudflare Pages** (unlimited bandwidth, edge SSD, instant Astro SSG build)
- **Backend API**: **Hugging Face Spaces** (Docker SDK, **16 GB RAM**, 2 vCPUs, zero cost, $0)
- **Automated Sync & Hot-Reload**: **GitHub Actions** weekly cron with auto-commit and Hugging Face webhook restart.

---

## 2. Comprehensive Inventory of Changes Made

### A. Groq Cloud LLM Synthesis Integration & Model Discovery
1. **API Key Integration & Model Calibration**:
   - Integrated Groq Cloud API credentials (`GROQ_API_KEY`) into the root `.env`, `frontend/.env`, and `.env.example`.
   - Probed the Groq API model catalog dynamically using `client.models.list()`. Configured **`qwen/qwen3.8-27b`** (active and operates within generous free-tier limits: 30 RPM, 8K TPM, 1K RPD).
   - Configured `backend/agents/synthesis.py` and `backend/main.py` with `GROQ_MODEL=qwen/qwen3.8-27b` as the default conversational model.
   - Verified live synthesis: Tested via `GET /health` (`retrieval=real`, `synthesis=real`, `graph_ready=true`) and live queries yielding grounded statutory and welfare answers with verified citations.

### B. Modern Minimalist UI / UX Redesign (OpenAI & Apple Aesthetics)
1. **Interactive Atmospheric Hero**:
   - Integrated React Bits `<GradientASCII />` canvas with fluid light-mode palette and horizon density.
   - Multi-point starbursts replaced with authentic hand-drawn 6-ray asterisks (`*`) scattered naturally across the canvas with subtle rotational tilts.
   - Underline accent on *"Verified by law."* calibrated with an exact 7-color rainbow spectrum positioned neatly under the punchline keyword.
2. **Scroll-Adaptive Floating Pill Navbar**:
   - Header begins completely transparent in the hero, seamlessly morphing on scroll (>180px) into a floating frosted glass pill (`max-w-6xl w-[95%] h-14 bg-white/85 backdrop-blur-xl rounded-full shadow-lg`).
   - Fixed character collision between the command glyph and `K` inside the `⌘K` shortcut badge.
   - Replaced all placeholder initials with the official CivicConnect 3D ribbon emblem.
3. **Continuous Scrubbed Scrollytelling & Staggered Cards**:
   - Pinned OpenAI Codex-style scrollytelling frame with expanding underline progress bars.
   - 3-card domain stack that spreads out horizontally on scroll.
   - 4-step methodology cards animate into view individually based on each card's real-time viewport progress (`cRect.top`).
4. **Chat Area Modernization & Local Persistence**:
   - Clean solid-color editorial headers without noisy badge pills.
   - Soft-pill prompt starter cards with micro-interaction hover arrows.
   - Deep charcoal user message bubbles and subtle off-white assistant message cards.
   - **Full Persistence (`localStorage`)**: Resolved history disappearing on page refresh. Conversation threads, citations, and custom titles now auto-persist and hydrate immediately.

### C. Database Schema, Welfare Schemes Enrichment & Indexing
1. **Full 18 Welfare Schemes Seeding**:
   - Ingested all 18 official Central and State welfare schemes (PMJDY, PM-KISAN, Ayushman Bharat PM-JAY, PMAY-U, PMUY, PMMVY, PM SVANidhi, Stand Up India, PM POSHAN, PM Vishwakarma, MP Ladli Laxmi Yojana, MP Ladli Behna, MP Kanya Vivah, Delhi Ladli, Delhi Disability Pension, Maharashtra Majhi Kanya, Tamil Nadu Pudhumai Penn, and Karnataka Gruha Lakshmi).
2. **Cryptographic Provenance Check (Issue #5 & Issue #18)**:
   - Validated that **zero LLM-generated or fabricated filler text** exists anywhere in the corpus (`chunks` table).
   - Ensured every statutory chunk and welfare chunk has deterministic text extraction, unique SHA-256 text hashes (`text_sha256`), and distinct raw source document hashes (`raw_sha256`).
3. **FAISS & BM25 Search Indices Rebuild**:
   - Re-embedded all 165 database chunks using `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional dense vectors).
   - Built and persisted: `data/indexing/artifacts/faiss.index`, `bm25.pkl`, and `chunk_ids.json`.

---

## 3. Production Hosting Architecture (100% Free)

```text
                                  USERS & BROWSERS
                                         │
                                         ▼
                     ┌───────────────────────────────────────┐
                     │           Astro Frontend              │
                     │      Hosted on Cloudflare Pages       │
                     │          (100% Free Tier)             │
                     └───────────────────┬───────────────────┘
                                         │
                                         │ HTTPS (REST API queries)
                                         ▼
                     ┌───────────────────────────────────────┐
                     │          FastAPI Backend              │
                     │    Hosted on Hugging Face Spaces      │
                     │     (16 GB RAM · 2 vCPUs · $0)        │
                     │     Docker SDK · Listening on 7860    │
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

## 4. Why Hugging Face Spaces (Gradio SDK - 100% Free) + Cloudflare Pages?

### A. Backend on Hugging Face Spaces (Gradio SDK):
1. **100% FREE Tier (No Credit Card / Zero Cost)**: Hugging Face Spaces par **Gradio SDK** default me **CPU Basic (2 vCPU · 16 GB RAM)** ke saath **100% Free** milta hai. (Docker option par unhone recent policy me paid/Pro badge lagaya hai, isliye hum native **Gradio SDK** use kar rahe hain).
2. **FastAPI Mounted Inside Gradio (`app.py`)**: Hugging Face Spaces Gradio SDK par humne `app.py` banaya hai jo hamari puri FastAPI application (`backend.main:app`) ko mount karta hai.
   - Saare REST endpoints (`/health`, `/api/query`, `/api/search`, `/docs`) seamlessly work karte hain.
   - Cloudflare Pages frontend directly in endpoints ko call karta hai.
   - Bonus: Space ke URL par ek clean live test UI bhi milta hai!
3. **16 GB RAM Available**: PyTorch, `sentence-transformers`, FAISS aur BM25 bina kisi memory crash (`OOM`) ke smooth chalte hain.

### B. Frontend on Cloudflare Pages:
1. **Global Anycast Edge Network**: Zero cold starts, ultra-low latency worldwide, and unlimited bandwidth on the free tier.
2. **Native Astro SSG Support**: Built directly from `frontend/` directory with static asset distribution.

---

## 5. Turnkey Deployment Walkthrough

### Step 1: Deploy Backend on Hugging Face Spaces (~3 minutes)

1. **Create Space**:
   - Go to [huggingface.co/spaces](https://huggingface.co/spaces) and click **Create new Space**.
   - **Space Name**: `civicconnect-api`
   - **License**: `mit` or `apache-2.0`
   - **Space SDK**: Select **Gradio** (100% Free).
   - **Hardware**: **CPU Basic (2 vCPU · 16 GB RAM · Free)**.
   - **Visibility**: **Public**.
   - Click **Create Space**.

2. **Push Code to Hugging Face**:
   In your local repository terminal:
   ```bash
   git remote add hf https://huggingface.co/spaces/<your-hf-username>/civicconnect-api
   git push hf main:main
   ```
   *(Hugging Face will automatically read `requirements.txt` and launch `app.py` with both Gradio & FastAPI).*

3. **Configure Environment Secrets & Variables on Hugging Face**:
   - In your Space, navigate to **Settings** &rarr; **Variables and secrets**.
   - Add the following secret:
     | Name | Value | Type |
     |---|---|---|
     | `GROQ_API_KEY` | `<your-groq-api-key>` | Secret |
   - Add the following variables:
     | Name | Value | Type |
     |---|---|---|
     | `GROQ_MODEL` | `qwen/qwen3.8-27b` | Variable |
     | `CORS_ORIGINS` | `*` | Variable |
     | `DATABASE_URL` | `sqlite:///./civicconnect.db` | Variable |
   - In your Space, navigate to **Settings** &rarr; **Variables and secrets**.
   - Add the following secret:
     - `GROQ_API_KEY`: `<your-groq-api-key>`
   - Add the following variables:
     - `GROQ_MODEL`: `qwen/qwen3.8-27b`
     - `CORS_ORIGINS`: `*`
     - `DATABASE_URL`: `sqlite:///./civicconnect.db`

4. **Verify Live Backend**:
   - Your Space URL is: `https://<your-hf-username>-civicconnect-api.hf.space`
   - Visit `https://<your-hf-username>-civicconnect-api.hf.space/health`
   - Expected JSON response:
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

### Step 2: Deploy Frontend on Cloudflare Pages (~2 minutes)

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com/) &rarr; **Workers & Pages** &rarr; **Create application** &rarr; **Pages** &rarr; **Connect to Git**.
2. Select repository: `Navya7275/CivicConnect`.
3. In **Build Settings**:
   - **Framework preset**: `Astro`
   - **Root directory**: `frontend`
   - **Build command**: `npm run build`
   - **Build output directory**: `dist`
4. In **Environment variables**:
   - `PUBLIC_USE_MOCK`: `false`
   - `PUBLIC_API_BASE`: `https://<your-hf-username>-civicconnect-api.hf.space`
5. Click **Save and Deploy**. Cloudflare will compile and provide a fast, secure HTTPS URL (e.g. `https://civicconnect.pages.dev`).

---

### Step 3: Configure Automated Sync & Hugging Face Auto-Reload

1. In Hugging Face, go to **Settings &rarr; Access Tokens** and create a token with `Write` role.
2. In your GitHub repository **Settings &rarr; Secrets and variables &rarr; Actions**, add two repository secrets:
   - `HF_TOKEN`: `<your-huggingface-access-token>`
   - `HF_SPACE_ID`: `<your-hf-username>/civicconnect-api`
3. Every Sunday at 02:00 AM UTC (or when triggered manually), the `.github/workflows/weekly-sync.yml` workflow:
   - Fetches newly published schemes from official sources.
   - Re-embeds new documents and commits the updated database back to `main`.
   - Calls the Hugging Face Spaces API restart endpoint (`/restart`), ensuring the live backend reloads seamlessly with fresh legal data.

---

## 6. Verification Checklist

- [x] Dockerfile exposes and binds to port `7860` for Hugging Face Spaces compatibility.
- [x] Cloudflare Pages root directory and build output set correctly (`frontend` / `dist`).
- [x] Groq LLM integration live with model `qwen/qwen3.8-27b`.
- [x] FAISS dense index & BM25 sparse index persisted and loaded.
- [x] Clean editorial typography and responsive centering across all pages.
- [x] Chat history persists across browser reloads via `localStorage`.
- [x] Zero compilation errors across both Python backend and Astro frontend.

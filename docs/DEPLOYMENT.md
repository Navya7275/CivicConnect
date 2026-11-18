# CivicConnect — Deployment Guide

This guide describes how to deploy the CivicConnect stack for demonstrations and production hosting.

> [!IMPORTANT]
> **Read this before following the Render or Railway steps below.** Those free
> tiers give 512 MB of RAM, which is not enough to load the sentence-transformers
> model: the container is OOM-killed during startup. The backend is intended to
> run on Hugging Face Spaces instead, which gives 2 vCPUs and 16 GB free.
>
> The Hugging Face route, with the environment variables it needs, is written up
> in [`whats_new-harshit.md`](../whats_new-harshit.md) sections 4 and 5. The
> Render and Railway instructions here still apply to any host with enough
> memory.

---

## Architecture Overview

CivicConnect consists of two independently deployable pieces:

```text
┌──────────────────────────────────────┐        ┌───────────────────────────────────────┐
│           Astro Frontend             │        │            FastAPI Backend            │
│  (Static build in frontend/dist/)    │ ─────> │   (Containerised API, LangGraph RAG,  │
│  Hosted on Vercel, Netlify, or Pages │  POST  │    FAISS + BM25, PostgreSQL / SQLite) │
│                                      │ /query │   Hosted on Render, Railway, or Fly   │
└──────────────────────────────────────┘        └───────────────────────────────────────┘
```

1. **Frontend**: Static site built with Astro and React islands. No server process required; deployable to any CDN (Vercel, Netlify, Cloudflare Pages, GitHub Pages).
2. **Backend**: FastAPI web service with LangGraph agent workflow, `sentence-transformers` embedding models, FAISS vector index, BM25 index, and Groq LLM synthesis.

---

## 1. Environment Variables & Secrets

Never commit secrets to git. All variables must be configured via the hosting provider's environment settings.

### Backend Environment Variables

| Variable | Required | Example / Default | Description |
|---|---|---|---|
| `GROQ_API_KEY` | **Yes** | `gsk_...` | Groq API key for Llama 3 synthesis agent. |
| `DATABASE_URL` | No | `sqlite:///./civicconnect.db` | PostgreSQL connection string or SQLite path. |
| `CORS_ORIGINS` | **Yes** | `https://civicconnect.vercel.app` | Comma-separated list of allowed frontend origins. |
| `PORT` | No | `8000` | Port assigned by hosting environment (Render/Railway bind automatically). |

> [!IMPORTANT]
> Ensure the deployed frontend domain (e.g. `https://your-frontend.vercel.app`) is included in `CORS_ORIGINS`, otherwise browser cross-origin requests will be blocked.

### Frontend Environment Variables (Build Time)

| Variable | Required | Default | Description |
|---|---|---|---|
| `PUBLIC_USE_MOCK` | **Yes** | `false` | Set to `false` in production build to connect to real backend. |
| `PUBLIC_API_BASE` | **Yes** | `https://api.yourdomain.com` | Public URL of deployed backend. Inlined at build time by Vite. |

---

## 2. Backend Deployment

### Option A: Deploy via Dockerfile (Recommended for Render, Railway, Fly.io)

A production-ready `Dockerfile` is provided at the repository root. It installs system dependencies, copies Python requirements, initializes the database, and pre-builds the FAISS/BM25 search indexes inside the container image so startup is fast and deterministic.

#### Render Deployment Steps:
1. Log into [Render](https://render.com) and create a **New Web Service**.
2. Connect the `Navya7275/CivicConnect` repository.
3. Select **Docker** environment (Render detects `Dockerfile` automatically).
4. Set Instance Type: Standard / at least 1 GB RAM (recommended 2 GB RAM for PyTorch / sentence-transformers).
5. Under **Environment Variables**, add:
   - `GROQ_API_KEY`: `<your_groq_api_key>`
   - `CORS_ORIGINS`: `https://<your-frontend>.vercel.app,http://localhost:4321`
6. Click **Deploy Web Service**.

#### Railway Deployment Steps:
1. Create a **New Project** on [Railway](https://railway.app).
2. Choose **Deploy from GitHub repo**.
3. Add `GROQ_API_KEY` and `CORS_ORIGINS` in project settings.
4. Railway builds the image from `Dockerfile` and assigns a public URL (`https://...up.railway.app`).

### Option B: HuggingFace Spaces (Free Tier ML Hosting)

HuggingFace Spaces handles large machine learning dependencies (`torch`, `sentence-transformers`, `faiss`) natively on its free tier:
1. Create a new Space on [Hugging Face](https://huggingface.co/spaces) with SDK type **Docker**.
2. Push repository code to the Space.
3. Configure `GROQ_API_KEY` and `CORS_ORIGINS` under Space Settings -> Variables and Secrets.

---

## 3. Frontend Deployment

### Deploy to Vercel / Netlify

1. In the Vercel/Netlify dashboard, create a **New Project** from GitHub.
2. Configure project directories:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
3. Configure Environment Variables:
   - `PUBLIC_USE_MOCK`: `false`
   - `PUBLIC_API_BASE`: `https://<your-deployed-backend-url>`
4. Click **Deploy**.

---

## 4. Fallback Live Demo Mode (Local Backend + Public Tunnel)

If cloud backend resources are unavailable or experience cold-start latency during a live presentation:

1. Run the backend locally with real database and API keys:
   ```bash
   # From repository root:
   python -m uvicorn backend.main:app --port 8000
   ```
2. Expose the port via a secure tunnel:
   ```bash
   # Using Cloudflare Tunnel:
   cloudflared tunnel --url http://localhost:8000
   
   # Or using ngrok:
   ngrok http 8000
   ```
3. Copy the generated HTTPS tunnel URL (e.g. `https://xyz.trycloudflare.com`).
4. Rebuild or deploy the frontend with `PUBLIC_API_BASE=https://xyz.trycloudflare.com` and `PUBLIC_USE_MOCK=false`.

---

## 5. Deployment Verification Checklist

Verify the deployed stack end-to-end:

1. **Check Backend Health**:
   ```bash
   curl -s https://<deployed-backend-url>/health
   ```
   Must return:
   ```json
   {
     "status": "healthy",
     "serving_real_answers": true,
     "database": "connected"
   }
   ```
2. **Test Query Endpoint**:
   ```bash
   curl -s -X POST https://<deployed-backend-url>/query \
     -H "Content-Type: application/json" \
     -d '{"query": "What is the RTI application response timeline?"}'
   ```
   Must return an answer citing the Right to Information Act, 2005 Section 7 with `verified: true`.
3. **Open Deployed Frontend**:
   - Ask an end-to-end question in the chat interface.
   - Verify that the **Verified Statutory Answer** badge appears.
   - Open the citation drawer and click the source link to verify it directs to the official government portal.

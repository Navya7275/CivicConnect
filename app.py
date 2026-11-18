"""CivicConnect — Hugging Face Gradio Space Entrypoint.

Hugging Face Spaces natively supports Gradio SDK on the 100% Free CPU Tier (16 GB RAM).
This entrypoint mounts our FastAPI backend (`backend.main:app`) into Gradio, exposing both:
1. All FastAPI REST API endpoints:
   - `POST /query` (primary legal & welfare assistant endpoint called by frontend)
   - `GET /health` (readiness and provider diagnostics)
   - `GET /docs` (interactive Swagger UI)
2. An interactive Gradio test interface directly at `/gradio` (or UI preview).
"""

from __future__ import annotations

# Imported ahead of gradio, torch and sentence-transformers on purpose. On
# ZeroGPU hardware this package patches CUDA initialisation, and it can only do
# that if nothing has touched CUDA before it loads.
import spaces

import logging
import os
import socket
import threading
from pathlib import Path
import gradio as gr

# Set writable cache directories for Hugging Face sandbox
os.environ.setdefault("TRANSFORMERS_CACHE", "/tmp/transformers_cache")
os.environ.setdefault("TORCH_HOME", "/tmp/torch_cache")
os.environ.setdefault("HF_HOME", "/tmp/hf_home")

logger = logging.getLogger("civicconnect.space")
logging.basicConfig(level=logging.INFO)


def _bootstrap_database_if_needed() -> None:
    """Ensure SQLite database and seed/welfare chunks are initialized on Space boot.
    
    Since civicconnect.db is gitignored and Dockerfile is bypassed on Gradio SDK,
    the Space starts without a database. Loading seed and welfare schemes builds the
    necessary tables and rows. The search indexes are then derived from those rows
    by _build_indexes_if_needed(), which runs straight after this.
    """
    db_path = Path("civicconnect.db")
    if not db_path.exists() or db_path.stat().st_size == 0:
        logger.info("Database file '%s' not found. Bootstrapping database...", db_path)
        try:
            from data.db.database import init_db
            from data.ingestion.load_seed import load_seed_data
            from data.ingestion.load_welfare import load_welfare_schemes

            init_db()
            load_seed_data()
            load_welfare_schemes()
            logger.info("Database successfully bootstrapped.")
        except Exception as exc:
            logger.exception("Failed to bootstrap database: %s", exc)
    else:
        logger.info("Database '%s' already exists (%d bytes).", db_path, db_path.stat().st_size)


def _build_indexes_if_needed() -> None:
    """Build the FAISS and BM25 artifacts when the container has none.

    The artifacts are deliberately not shipped to the Space, because neither way
    of shipping them works. Pushed as ordinary files, Hugging Face rejects the
    push outright -- "your push was rejected because it contains binary files",
    whatever their size. Pushed through git LFS, the push succeeds and the files
    then do not exist in the running container: the first deploy reported
    `BM25 index not found: /app/data/indexing/artifacts/bm25.pkl` while
    seed_schemes.json in the directory beside it loaded perfectly.

    They are derived data anyway. build_indexes() reads the chunks table that
    _bootstrap_database_if_needed() has just populated and writes both indexes
    from it, which is exactly what the Dockerfile does at image build time.
    Deriving them here has a second benefit: they cannot go stale against the
    corpus, because they are built from the corpus that was just loaded.

    The cost is one embedding-model download and the embedding of ~960 short
    chunks on each cold start. Nothing is rebuilt when the artifacts are already
    present, which is the normal case for a local checkout.
    """
    from data.indexing.build_index import ARTIFACTS_DIR

    required = ["faiss.index", "bm25.pkl", "chunk_ids.json"]
    missing = [name for name in required if not (ARTIFACTS_DIR / name).exists()]
    if not missing:
        logger.info("Index artifacts present in %s; not rebuilding.", ARTIFACTS_DIR)
        return

    logger.info(
        "Index artifacts missing (%s). Building them from the chunks table; "
        "this takes a short while on a cold start...", ", ".join(missing))
    try:
        from data.indexing.build_index import build_indexes

        build_indexes()
        logger.info("Index artifacts built. Retrieval should now load for real.")
    except (Exception, SystemExit) as exc:  # noqa: BLE001
        # build_indexes() raises SystemExit when the chunks table is missing or
        # empty, which `except Exception` would not catch -- and an uncaught
        # SystemExit here would take the whole Space down instead of leaving it
        # serving stubs with an explanation.
        logger.exception("Could not build index artifacts: %s", exc)


# Bootstrap database and derive the search indexes before the FastAPI app is
# imported, since its startup is what loads the retrieval provider.
_bootstrap_database_if_needed()
_build_indexes_if_needed()

from backend.main import app as fastapi_app
from backend.orchestration.state import initial_state


def query_civicconnect(question: str):
    """Gradio test harness query function using compiled orchestration graph."""
    if not question.strip():
        return "Please enter a valid question regarding Indian laws or welfare schemes."

    graph = getattr(fastapi_app.state, "graph", None)
    if graph is None:
        return "⚠️ Orchestration graph is still compiling or unavailable. Please check backend /health."

    try:
        state = initial_state(question)
        final_state = graph.invoke(state)

        if final_state.get("needs_clarification"):
            return f"ℹ️ **Clarification Needed:** {final_state.get('clarification_question')}"

        answer = final_state.get("draft_answer") or final_state.get("answer") or "No answer generated."
        citations = final_state.get("citations", [])
        verified = final_state.get("verified", False)

        formatted = f"{answer}\n\n---\n**Verification Status:** {'✅ Verified by law' if verified else '⚠️ Unverified'}\n"
        if citations:
            formatted += "\n**Statutory Citations / Sources:**\n"
            for c in citations:
                act = c.get("act", "")
                section = c.get("section", "")
                jurisdiction = c.get("jurisdiction", "")
                label = f"{act} Section {section}" if section else act
                if jurisdiction:
                    label += f" ({jurisdiction})"
                url = c.get("reference_url") or c.get("source_url")
                if url:
                    formatted += f"- [{label}]({url})\n"
                else:
                    formatted += f"- {label}\n"

        return formatted
    except Exception as e:
        logger.exception("Error executing query through graph")
        return f"Error processing query: {str(e)}"


# --- ZeroGPU's startup requirement -----------------------------------------
# The free Gradio tier runs on ZeroGPU, and that runtime scans the app at
# startup for at least one function decorated with @spaces.GPU. Finding none it
# stops the Space with "No @spaces.GPU function detected during startup", which
# is how the first deploy ended: the corpus loaded, the graph compiled, and then
# the Space was killed for not asking for a GPU.
#
# CivicConnect genuinely wants no GPU. Retrieval is FAISS over 384-dimensional
# vectors and synthesis is an HTTP call to Groq, so every part of the answer
# path is CPU-bound or remote. This function exists to satisfy that check and
# to report what the runtime handed us; nothing in the answer path calls it, and
# on CPU hardware the decorator does nothing at all.
@spaces.GPU(duration=15)
def gpu_selftest() -> str:
    """Report the torch/CUDA the Space runtime provided. Not used for answers."""
    import torch

    return f"torch {torch.__version__}, cuda available: {torch.cuda.is_available()}"


# Minimalist Gradio UI wrapper for test & verification
demo = gr.Interface(
    fn=query_civicconnect,
    inputs=gr.Textbox(
        lines=3,
        placeholder="Ask a question about Indian legal statutes, penalties, or welfare schemes...",
        label="CivicConnect Query",
    ),
    outputs=gr.Markdown(label="Answer & Grounded Citations"),
    title="CivicConnect API & Assistant",
    description="Grounded AI Assistant for Indian Statutory Law & Welfare Schemes. FastAPI endpoints active at `/docs`, `/health`, and `/query`.",
)

# Mount Gradio onto the FastAPI app so both coexist on port 7860.
#
# ssr_mode=False is load-bearing, and the reason the first two deploys served
# nothing. A Space sets GRADIO_SSR_MODE=True and GRADIO_SERVER_PORT=7860, and
# gradio's node_server.py starts its port search at GRADIO_SERVER_PORT. So with
# SSR left on, mount_gradio_app quietly starts a Node front proxy that binds
# 7860 -- the very port this app is meant to serve -- and uvicorn then finds it
# taken. That is the "[Errno 98] address already in use" from the first deploy,
# and the "Port 7860 is already being served" from the second. The culprit was
# inside this process all along, not elsewhere on the machine.
#
# Server-side rendering only speeds up the first paint of the Gradio page, which
# here is an internal test harness, and it needs a newer Node than the image
# carries anyway. FastAPI owning the port is what matters, because /health and
# /query are what the Cloudflare frontend calls.
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio", ssr_mode=False)

def _port_is_available(port: int) -> bool:
    """Whether this process can bind `port` itself.

    On the first Space deploy the app loaded cleanly -- 945 chunks, graph
    compiled -- and then died on "[Errno 98] error while attempting to bind on
    address ('0.0.0.0', 7860): address already in use". Something in the Space
    runtime was already serving that port, and uvicorn's failure to bind takes
    the whole process down with it.

    Checking first means we either serve the port or stand aside, rather than
    exiting and leaving the Space with nothing running at all.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("0.0.0.0", port))
        except OSError:
            return False
    return True


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    if _port_is_available(port):
        import uvicorn

        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        # Whatever already holds the port serves `app`, which is built and
        # mounted by the time we get here. Stay alive so the container is not
        # reaped, and say so plainly in the log rather than dying quietly.
        logger.warning(
            "Port %d is already being served; not starting a second server on "
            "it. The FastAPI app and the Gradio UI at /gradio are mounted.",
            port,
        )
        threading.Event().wait()

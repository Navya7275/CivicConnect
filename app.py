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
    necessary tables and rows. (Vector indexing artifacts are already tracked in git).
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


# Bootstrap database before FastAPI app or providers load
_bootstrap_database_if_needed()

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

# Mount Gradio onto the FastAPI app so both coexist on port 7860
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

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

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

import logging
import os
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

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)

"""CivicConnect — Hugging Face Gradio Space Entrypoint.

Hugging Face Spaces natively supports Gradio SDK on the 100% Free CPU Tier (16 GB RAM).
This entrypoint mounts our FastAPI backend (`backend.main:app`) into Gradio, exposing both:
1. All FastAPI REST API endpoints:
   - `/health`
   - `/api/query`
   - `/api/search`
   - `/api/schemes`
   - `/api/acts`
   - `/docs` (Swagger UI)
2. An interactive Gradio chat interface directly at `/gradio` or root for easy debugging.
"""

from __future__ import annotations

import os
import gradio as gr
from backend.main import app as fastapi_app
import requests

# Set writable cache directories for Hugging Face sandbox
os.environ.setdefault("TRANSFORMERS_CACHE", "/tmp/transformers_cache")
os.environ.setdefault("TORCH_HOME", "/tmp/torch_cache")
os.environ.setdefault("HF_HOME", "/tmp/hf_home")


def query_civicconnect(question: str):
    """Simple Gradio test harness query function."""
    if not question.strip():
        return "Please enter a valid question regarding Indian laws or welfare schemes."
    
    try:
        from backend.orchestration.graph import run_query
        result = run_query(question)
        answer = result.get("answer", "No answer generated.")
        sources = result.get("sources", [])
        if sources:
            answer += "\n\n**Sources / Citations:**\n"
            for src in sources:
                answer += f"- {src.get('title', 'Document')} ({src.get('source_type', 'Reference')})\n"
        return answer
    except Exception as e:
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
    description="Grounded AI Assistant for Indian Statutory Law & Welfare Schemes. FastAPI endpoints active at `/docs`, `/health`, and `/api/*`.",
)

# Mount Gradio onto the FastAPI app so both coexist on port 7860
# FastAPI handles API calls from Cloudflare Pages, Gradio provides UI preview
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)

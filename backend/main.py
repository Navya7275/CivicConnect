"""CivicConnect API entrypoint.

Run it with:

    uvicorn backend.main:app --reload

Then open http://localhost:8000/docs for the interactive API documentation.

Phase C1 note: the graph runs end to end, but retrieval and synthesis are
stubs. Answers come back clearly labelled "STUB". Real answers arrive in
Phase C2, when Ayushi's retriever and synthesis agent are wired in — that is a
change to `build_graph()` below, not to any of the agents.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import VERSION, router
from backend.orchestration.graph import build_graph

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s  %(levelname)-8s %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


def _cors_origins() -> list[str]:
    """Read allowed CORS origins from the environment.

    Defaults cover the Astro dev server (4321) and a plain Vite/CRA port (3000).
    """
    raw = os.getenv("CORS_ORIGINS", "http://localhost:4321,http://localhost:3000")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Compile the orchestration graph once at startup, not per request.

    Building the graph is cheap today, but once the real retriever is attached
    it will load an embedding model and index files. Doing that once here keeps
    the first request from paying for it.
    """
    logger.info("Starting CivicConnect API v%s", VERSION)

    # Phase C2: pass the real implementations here, for example
    #     build_graph(retriever=HybridRetriever(), synthesizer=SynthesisAgent())
    app.state.graph = build_graph()

    logger.info("Orchestration graph ready.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="CivicConnect API",
    description=(
        "A multi-agent, hybrid-RAG assistant that answers questions about "
        "Indian law and welfare schemes, grounded in real statutory sources."
    ),
    version=VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    """Point people at the docs instead of returning a bare 404."""
    return {
        "service": "CivicConnect API",
        "version": VERSION,
        "docs": "/docs",
        "health": "/health",
    }

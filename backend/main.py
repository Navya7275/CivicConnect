"""CivicConnect API entrypoint.

Run it with:

    uvicorn backend.main:app --reload

Then open http://localhost:8000/docs for the interactive API documentation.

Phase C2: the app loads the real retriever and synthesis agent at startup when
they are available, and falls back to clearly-labelled stubs when they are not.
`GET /health` reports which, so you can always tell whether an answer came from
real law or a placeholder. Nothing here needs changing as those components land
— they are picked up automatically.
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
from backend.orchestration.providers import load_all

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
    """Load the real components and compile the graph, once, at startup.

    Doing this here rather than per request matters: the real retriever loads an
    embedding model and reads the FAISS index from disk, which is far too slow to
    repeat on every question.

    Anything unavailable falls back to a stub and is reported on `/health`, so
    the API always starts and always says what it is actually serving.
    """
    logger.info("Starting CivicConnect API v%s", VERSION)

    retriever, synthesizer, query_logger, status = load_all()

    app.state.graph = build_graph(retriever=retriever, synthesizer=synthesizer)
    app.state.query_logger = query_logger
    app.state.provider_status = status

    logger.info(
        "Ready. retrieval=%s synthesis=%s query_log=%s",
        status.retrieval,
        status.synthesis,
        status.query_logging,
    )
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

"""Provider loading for Phase C2 — connecting the real retrieval and synthesis.

Phase C1 ran the graph on stubs. Phase C2 swaps in the real components. The
awkward part is that those components live in other people's folders and depend
on things that may not be present: a populated database, a built FAISS index, a
Groq API key.

So rather than importing them at module level and crashing the whole API when
one is missing, each loader here *tries*, and reports back what happened. The
app then runs with whatever is actually available and says so on `/health`.

That matters for three reasons:

1. A teammate can run the API without a database and still get a working
   `/query` to develop the frontend against.
2. When something is missing we say exactly what, instead of a stack trace at
   startup.
3. The moment retrieval (#6) and the data layer land on `main`, this picks them
   up with no code change — the fallbacks simply stop being used.

Each loader returns `(component_or_None, status)` where `status` is a short
human-readable string that ends up in the health endpoint.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

from backend.orchestration.nodes import Retriever, Synthesizer

logger = logging.getLogger(__name__)

#: Reported on /health when a real component is in use.
STATUS_REAL = "real"


@dataclass
class ProviderStatus:
    """What the app managed to load, for diagnostics and `/health`."""

    retrieval: str
    synthesis: str
    query_logging: str

    @property
    def fully_real(self) -> bool:
        """True only when retrieval and synthesis are both the real thing."""
        return self.retrieval == STATUS_REAL and self.synthesis == STATUS_REAL


def load_retriever() -> tuple[Retriever | None, str]:
    """Try to build the real hybrid retriever.

    Needs, in order: the retrieval package to be importable, the FAISS and BM25
    artifacts to exist under `data/indexing/artifacts/`, and the chunks table to
    be populated.

    Returns:
        `(retriever, status)`. `retriever` is None when anything was missing,
        in which case the graph falls back to its stub.
    """
    try:
        from backend.retrieval.hybrid_search import HybridRetriever
    except Exception as exc:  # noqa: BLE001 - any import problem means "not available"
        reason = f"unavailable: retrieval package not importable ({exc.__class__.__name__}: {exc})"
        logger.warning("Retrieval: %s", reason)
        return None, reason

    try:
        retriever = HybridRetriever()
    except FileNotFoundError as exc:
        reason = f"unavailable: index artifacts missing ({exc})"
        logger.warning("Retrieval: %s", reason)
        return None, reason
    except Exception as exc:  # noqa: BLE001 - e.g. no database, empty chunks table
        reason = f"unavailable: could not initialise ({exc.__class__.__name__}: {exc})"
        logger.warning("Retrieval: %s", reason)
        return None, reason

    logger.info("Retrieval: real hybrid retriever loaded.")
    return retriever, STATUS_REAL


def load_synthesizer() -> tuple[Synthesizer | None, str]:
    """Try to build the real synthesis agent.

    Needs the agent to be importable and `GROQ_API_KEY` to be set. We check the
    key ourselves rather than letting the Groq client raise, so the message says
    what to do about it.
    """
    if not os.getenv("GROQ_API_KEY"):
        reason = "unavailable: GROQ_API_KEY is not set"
        logger.warning("Synthesis: %s", reason)
        return None, reason

    try:
        from backend.agents.synthesis import SynthesisAgent
    except Exception as exc:  # noqa: BLE001
        reason = f"unavailable: synthesis agent not importable ({exc.__class__.__name__}: {exc})"
        logger.warning("Synthesis: %s", reason)
        return None, reason

    try:
        synthesizer = SynthesisAgent()
    except Exception as exc:  # noqa: BLE001
        reason = f"unavailable: could not initialise ({exc.__class__.__name__}: {exc})"
        logger.warning("Synthesis: %s", reason)
        return None, reason

    logger.info("Synthesis: real agent loaded.")
    return synthesizer, STATUS_REAL


def load_query_logger() -> tuple[Any | None, str]:
    """Try to load the query-logging helper (C2.3).

    Writes each query, answer, cited chunk ids and verification verdict to the
    `query_logs` table. Lives in the data layer, so it is unavailable until that
    lands on `main`.

    Returns:
        `(log_callable, status)` where `log_callable(**kwargs)` persists one row.
    """
    try:
        from data.db.database import SessionLocal
        from data.db.logger import log_query
    except Exception as exc:  # noqa: BLE001
        reason = f"unavailable: data layer not importable ({exc.__class__.__name__}: {exc})"
        logger.warning("Query logging: %s", reason)
        return None, reason

    def persist(
        query: str,
        answer: str,
        cited_chunk_ids: list[str],
        verified: bool,
        state: str | None,
    ) -> None:
        """Write one query_logs row, swallowing failures.

        A logging failure must never turn a good answer into a 500, so this
        reports and moves on rather than propagating.
        """
        session = SessionLocal()
        try:
            log_query(
                session,
                query=query,
                answer=answer,
                cited_chunk_ids=cited_chunk_ids,
                verified=verified,
                state=state,
            )
        except Exception:  # noqa: BLE001
            logger.exception("Failed to write query log; continuing.")
        finally:
            session.close()

    logger.info("Query logging: enabled.")
    return persist, STATUS_REAL


def load_all() -> tuple[Retriever | None, Synthesizer | None, Any | None, ProviderStatus]:
    """Load every provider and summarise what we got.

    Called once at startup. Logs a short summary so it is obvious from the
    console whether the API is serving real answers or stubs.
    """
    retriever, retrieval_status = load_retriever()
    synthesizer, synthesis_status = load_synthesizer()
    query_logger, logging_status = load_query_logger()

    status = ProviderStatus(
        retrieval=retrieval_status,
        synthesis=synthesis_status,
        query_logging=logging_status,
    )

    if status.fully_real:
        logger.info("Phase C2 active: /query returns real grounded answers.")
    else:
        logger.warning(
            "Phase C2 incomplete — /query is serving stub data.\n"
            "  retrieval : %s\n"
            "  synthesis : %s\n"
            "  query log : %s",
            status.retrieval,
            status.synthesis,
            status.query_logging,
        )

    return retriever, synthesizer, query_logger, status

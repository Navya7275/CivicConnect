"""Node functions for the orchestration graph.

Each node takes the current `GraphState` and returns only the keys it changes.

Phase C1 status:
  - `query_understanding_node` is real and complete.
  - `retrieval_node`, `synthesis_node` and `verification_node` are stubs that
    return mock data, exactly as `docs/PHASES.md` C1.2 asks for.

The stubs are not thrown away in Phase C2. Each node calls a small provider
function, and `build_graph()` lets you pass a real implementation in place of
the stub. So wiring in Ayushi's retriever later is a constructor argument, not
a rewrite of this file.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Protocol

from backend.agents.query_understanding import QueryUnderstandingAgent
from backend.orchestration.state import MAX_RETRIES, GraphState

logger = logging.getLogger(__name__)

_agent = QueryUnderstandingAgent()


# --------------------------------------------------------------------------
# Provider interfaces
#
# These describe what Phase C2 has to plug in. Defining them now means the
# graph does not need to change when the real implementations arrive.
# --------------------------------------------------------------------------

class Retriever(Protocol):
    """What the graph needs from the retrieval layer.

    Ayushi's `HybridRetriever.search()` already has this signature (PR #6),
    including the optional `as_of_date` added for issue #2 item B5.
    """

    def search(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        ...


class Synthesizer(Protocol):
    """What the graph needs from the synthesis agent.

    Ayushi's `SynthesisAgent.synthesize()` matches this as of PR #6, which
    renamed its `sources` key to `citations` (issue #2 item B6).
    """

    def synthesize(
        self,
        query: str,
        retrieved_chunks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        ...


# --------------------------------------------------------------------------
# Stub implementations (Phase C1)
# --------------------------------------------------------------------------

_STUB_CHUNK: dict[str, Any] = {
    "chunk_id": "stub-000",
    "text": (
        "STUB CHUNK — this is placeholder text from the Phase C1 orchestration "
        "skeleton, not real law. Real chunks arrive in Phase C2."
    ),
    "act": "STUB — not a real Act",
    "chapter": "",
    "section": "STUB",
    "jurisdiction": "Central",
    "effective_date": "1970-01-01",
    "source_url": "https://example.invalid/stub",
}


def _stub_search(
    query: str,
    filters: dict[str, Any] | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Stand-in retriever for Phase C1.

    Returns one obviously-fake chunk. It is labelled 'STUB' in every field and
    points at `example.invalid`, a reserved domain that can never resolve, so
    that placeholder data can never be mistaken for a real citation if it leaks
    into the UI by accident.
    """
    logger.warning("Using STUB retriever — no real search is happening (Phase C1).")
    chunk = dict(_STUB_CHUNK)
    if filters and filters.get("jurisdiction"):
        chunk["jurisdiction"] = filters["jurisdiction"]
    return [chunk][:limit]


def _stub_synthesize(
    query: str,
    retrieved_chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    """Stand-in synthesis agent for Phase C1.

    Does not call an LLM. Returns a fixed message plus citations built from
    whatever chunks it was handed, so the response shape is realistic even
    though the content is not.
    """
    logger.warning("Using STUB synthesizer — no LLM is being called (Phase C1).")

    if not retrieved_chunks:
        return {
            "answer": "The available sources do not contain enough information to answer this question.",
            "citations": [],
        }

    return {
        "answer": (
            "STUB ANSWER — the orchestration graph ran end to end, but synthesis "
            "is not wired up yet (Phase C2). Your question was: "
            f"'{query}'"
        ),
        "citations": [
            {
                "act": chunk["act"],
                "section": chunk["section"],
                "jurisdiction": chunk["jurisdiction"],
                "source_url": chunk["source_url"],
                "chunk_id": chunk.get("chunk_id"),
            }
            for chunk in retrieved_chunks
        ],
    }


# --------------------------------------------------------------------------
# Nodes
# --------------------------------------------------------------------------

def query_understanding_node(state: GraphState) -> GraphState:
    """Work out intent and jurisdiction, and decide whether we can proceed.

    This node is fully implemented. If the question is about an area of law
    that varies by state and we do not know the user's state, it sets
    `needs_clarification` and the graph stops here rather than guessing.
    """
    result = _agent.understand(
        query=state.get("query", ""),
        state=state.get("state"),
    )

    logger.info(
        "Query understood: intent=%s jurisdiction=%s needs_clarification=%s",
        result.intent,
        result.jurisdiction,
        result.needs_clarification,
    )

    return GraphState(
        intent=result.intent,
        jurisdiction=result.jurisdiction,
        rewritten_query=result.rewritten_query,
        needs_clarification=result.needs_clarification,
        clarification_question=result.clarification_question,
    )


def make_retrieval_node(retriever: Retriever | None = None) -> Callable[[GraphState], GraphState]:
    """Build the retrieval node.

    Args:
        retriever: The real retriever. When None, the Phase C1 stub is used.
    """
    search = retriever.search if retriever is not None else _stub_search

    def retrieval_node(state: GraphState) -> GraphState:
        """Fetch the chunks most relevant to the question."""
        jurisdiction = state.get("jurisdiction") or "Central"

        # The retriever is responsible for also including Central law when a
        # state is requested — see issue #2 item B3. We pass the state through
        # and let the retrieval layer apply that rule.
        filters = {"jurisdiction": jurisdiction}

        try:
            chunks = search(
                state.get("rewritten_query") or state.get("query", ""),
                filters=filters,
                limit=5,
            )
        except Exception as exc:  # noqa: BLE001 - we want any failure surfaced as state
            logger.exception("Retrieval failed")
            return GraphState(retrieved_chunks=[], error=f"retrieval failed: {exc}")

        logger.info("Retrieved %d chunks", len(chunks))
        return GraphState(retrieved_chunks=list(chunks))

    return retrieval_node


def make_synthesis_node(synthesizer: Synthesizer | None = None) -> Callable[[GraphState], GraphState]:
    """Build the synthesis node.

    Args:
        synthesizer: The real synthesis agent. When None, the Phase C1 stub is used.
    """
    synthesize = synthesizer.synthesize if synthesizer is not None else _stub_synthesize

    def synthesis_node(state: GraphState) -> GraphState:
        """Write a plain-language answer grounded in the retrieved chunks."""
        try:
            result = synthesize(
                state.get("query", ""),
                state.get("retrieved_chunks", []),
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Synthesis failed")
            return GraphState(
                draft_answer="",
                citations=[],
                error=f"synthesis failed: {exc}",
            )

        # Accept "sources" as well as "citations" so the graph keeps working
        # against any synthesis agent predating issue #2 item B6.
        citations = result.get("citations")
        if citations is None:
            citations = result.get("sources", [])

        return GraphState(
            draft_answer=result.get("answer", ""),
            citations=list(citations),
        )

    return synthesis_node


def verification_node(state: GraphState) -> GraphState:
    """Check that every citation points at a section we actually retrieved.

    Phase C1 keeps this simple: a citation counts as grounded when its
    `chunk_id` matches a retrieved chunk, or failing that when its act and
    section match one. Phase C3 replaces this with proper extraction of section
    numbers from the answer text plus a bounded retry loop.
    """
    chunks = state.get("retrieved_chunks", [])
    citations = state.get("citations", [])

    if not citations:
        # Nothing was cited. That is not a verification failure on its own —
        # "we don't have enough information" is a legitimate answer.
        return GraphState(verification_status="skipped", verified=False)

    known_ids = {chunk.get("chunk_id") for chunk in chunks if chunk.get("chunk_id")}
    known_sections = {
        (chunk.get("act"), chunk.get("section"))
        for chunk in chunks
    }

    ungrounded = [
        citation
        for citation in citations
        if citation.get("chunk_id") not in known_ids
        and (citation.get("act"), citation.get("section")) not in known_sections
    ]

    if ungrounded:
        logger.warning("Verification found %d ungrounded citation(s)", len(ungrounded))
        return GraphState(verification_status="ungrounded", verified=False)

    return GraphState(verification_status="verified", verified=True)


# --------------------------------------------------------------------------
# Routing
# --------------------------------------------------------------------------

def route_after_understanding(state: GraphState) -> str:
    """Stop and ask the user, or carry on and search."""
    return "clarify" if state.get("needs_clarification") else "retrieve"


def route_after_verification(state: GraphState) -> str:
    """Retry synthesis when citations were not grounded, up to `MAX_RETRIES`."""
    if state.get("verification_status") != "ungrounded":
        return "done"

    if state.get("retry_count", 0) >= MAX_RETRIES:
        logger.warning("Retry limit reached; returning the answer marked unverified.")
        return "done"

    return "retry"


def increment_retry_node(state: GraphState) -> GraphState:
    """Bump the retry counter before looping back to synthesis."""
    return GraphState(retry_count=state.get("retry_count", 0) + 1)

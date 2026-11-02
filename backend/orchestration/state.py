"""The shared state object that flows through the orchestration graph.

Every node receives this dictionary, reads what it needs, and returns only the
keys it wants to change. LangGraph merges those changes back in, so a node
never has to rebuild the whole state.

Field list follows `docs/PROJECT_PLAN.md` Appendix A point 4, with a few extras
we need in practice (the clarification question, and an error slot).
"""

from __future__ import annotations

from typing import Any, TypedDict

#: How many times synthesis may be retried when verification fails.
#: Beyond this we return the answer marked unverified rather than looping.
MAX_RETRIES = 2


class GraphState(TypedDict, total=False):
    """State passed between nodes.

    `total=False` means every key is optional, so a node can return a partial
    update without having to supply the rest.
    """

    # --- input ---
    query: str
    """The user's original question, exactly as they typed it."""

    state: str | None
    """The state the user selected in the UI, if any."""

    # --- set by query_understanding ---
    intent: str
    """Area of law: consumer, welfare, housing, labour, rti, traffic, police, general."""

    jurisdiction: str
    """Whose law applies: 'Central', a state name, or 'Unknown' when we must ask."""

    rewritten_query: str
    """The question after light normalisation, used for retrieval."""

    needs_clarification: bool
    """True when we cannot answer safely without knowing the user's state."""

    clarification_question: str | None
    """The question we ask the user when `needs_clarification` is True."""

    # --- set by retrieval ---
    retrieved_chunks: list[dict[str, Any]]
    """Chunks returned by the hybrid retriever, in the shape agreed in section 3."""

    # --- set by synthesis ---
    draft_answer: str
    """The generated answer, before verification."""

    citations: list[dict[str, Any]]
    """Sources backing the draft answer."""

    # --- set by verification ---
    verification_status: str
    """One of: 'pending', 'verified', 'ungrounded', 'skipped'."""

    verified: bool
    """True when every cited section was found in the retrieved chunks."""

    ungrounded_citations: list[dict[str, Any]]
    """Citation entries with no matching retrieved chunk."""

    hallucinated_sections: list[str]
    """Section numbers written in the answer prose with no supporting chunk.

    The headline number for our central claim. Phase E reports these as the
    hallucination rate (issue #13); they are not exposed on the API response,
    because the response shape is fixed by PROJECT_PLAN.md section 3.
    """

    checked_sections: list[str]
    """Every section number found in the prose, grounded or not."""

    retry_count: int
    """How many times synthesis has been re-run for this query."""

    # --- diagnostics ---
    error: str | None
    """Set when a node failed, so the API can return something useful."""


def initial_state(query: str, state: str | None = None) -> GraphState:
    """Build the starting state for one query.

    Everything downstream assumes these defaults exist, so create state through
    this function rather than building the dictionary by hand.
    """
    return GraphState(
        query=query,
        state=state,
        intent="",
        jurisdiction="",
        rewritten_query="",
        needs_clarification=False,
        clarification_question=None,
        retrieved_chunks=[],
        draft_answer="",
        citations=[],
        verification_status="pending",
        verified=False,
        ungrounded_citations=[],
        hallucinated_sections=[],
        checked_sections=[],
        retry_count=0,
        error=None,
    )

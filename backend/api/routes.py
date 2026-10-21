"""HTTP routes for CivicConnect.

Two endpoints, both defined in `docs/PROJECT_PLAN.md` section 3:

    POST /query    run a question through the orchestration graph
    GET  /health   liveness check

This module is deliberately thin. It converts HTTP into graph state, runs the
graph, and converts the final state back into the agreed response shape. All
the actual reasoning lives in the agents.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from backend.api.schemas import Citation, HealthResponse, QueryRequest, QueryResponse
from backend.orchestration.state import GraphState, initial_state

logger = logging.getLogger(__name__)

router = APIRouter()

VERSION = "0.1.0"


def _to_response(state: GraphState) -> QueryResponse:
    """Turn the graph's final state into the API response.

    Kept separate from the route so it can be tested without HTTP.
    """
    # When we need the user's state, the clarification question *is* the
    # answer. There is nothing to cite, and nothing has been verified.
    if state.get("needs_clarification"):
        return QueryResponse(
            answer=state.get("clarification_question") or "Which state or union territory are you asking about?",
            citations=[],
            jurisdiction=state.get("jurisdiction") or "Unknown",
            verified=False,
            needs_clarification=True,
        )

    citations = [
        Citation(
            act=raw.get("act", ""),
            section=raw.get("section", ""),
            jurisdiction=raw.get("jurisdiction", state.get("jurisdiction", "")),
            source_url=raw.get("source_url", ""),
            chunk_id=raw.get("chunk_id"),
            excerpt=raw.get("excerpt"),
        )
        for raw in state.get("citations", [])
    ]

    return QueryResponse(
        answer=state.get("draft_answer", ""),
        citations=citations,
        jurisdiction=state.get("jurisdiction") or "Central",
        verified=bool(state.get("verified", False)),
        needs_clarification=False,
    )


@router.post("/query", response_model=QueryResponse, summary="Ask a civic or legal question")
async def post_query(payload: QueryRequest, request: Request) -> QueryResponse:
    """Run one question through the full agent pipeline.

    Returns an answer with citations, or a clarification question when the law
    in question differs by state and we do not know which state the user is in.
    """
    graph = getattr(request.app.state, "graph", None)
    if graph is None:
        raise HTTPException(status_code=503, detail="Orchestration graph is not available")

    logger.info("Query received (state=%s): %s", payload.state, payload.query[:120])

    try:
        final_state = graph.invoke(initial_state(payload.query, payload.state))
    except Exception as exc:  # noqa: BLE001
        logger.exception("Graph execution failed")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {exc}") from exc

    if final_state.get("error"):
        logger.error("Graph finished with an error: %s", final_state["error"])
        raise HTTPException(status_code=500, detail=final_state["error"])

    return _to_response(final_state)


@router.get("/health", response_model=HealthResponse, summary="Service health check")
async def get_health(request: Request) -> HealthResponse:
    """Report whether the service is up and the graph compiled."""
    return HealthResponse(
        status="ok",
        version=VERSION,
        graph_ready=getattr(request.app.state, "graph", None) is not None,
    )

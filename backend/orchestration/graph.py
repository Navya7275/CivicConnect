"""The CivicConnect orchestration graph.

Wires the agents together as a LangGraph state machine:

    START
      |
      v
    query_understanding
      |
      +--(needs a state)--> END          # ask the user which state, answer nothing
      |
      v
    retrieval
      |
      v
    synthesis  <--------+
      |                 |
      v                 |
    verification        |
      |                 |
      +--(ungrounded)-->+ increment_retry   (up to MAX_RETRIES)
      |
      v
     END

Two things make this more than a straight line, and both are the point of the
project rather than decoration:

1. **The clarification exit.** If the question is about an area of law that
   differs by state and we do not know the user's state, we stop and ask. We do
   not guess.

2. **The verification loop.** If the answer cites a section that was not in the
   retrieved sources, we send it back to be written again. After `MAX_RETRIES`
   we give up and return the answer marked `verified: false`, rather than
   looping forever or quietly passing off an unchecked answer as checked.
"""

from __future__ import annotations

import logging

from langgraph.graph import END, START, StateGraph

from backend.orchestration.nodes import (
    Retriever,
    Synthesizer,
    increment_retry_node,
    make_retrieval_node,
    make_synthesis_node,
    query_understanding_node,
    route_after_understanding,
    route_after_verification,
    verification_node,
)
from backend.orchestration.state import GraphState

logger = logging.getLogger(__name__)


def build_graph(
    retriever: Retriever | None = None,
    synthesizer: Synthesizer | None = None,
):
    """Build and compile the orchestration graph.

    Args:
        retriever: Real retrieval implementation. When None, a clearly-labelled
            stub is used (Phase C1). Phase C2 passes Ayushi's `HybridRetriever`.
        synthesizer: Real synthesis agent. When None, a stub is used.
            Phase C2 passes Ayushi's `SynthesisAgent`.

    Returns:
        A compiled LangGraph app. Call `.invoke(initial_state(...))` on it.
    """
    builder = StateGraph(GraphState)

    builder.add_node("query_understanding", query_understanding_node)
    builder.add_node("retrieval", make_retrieval_node(retriever))
    builder.add_node("synthesis", make_synthesis_node(synthesizer))
    builder.add_node("verification", verification_node)
    builder.add_node("increment_retry", increment_retry_node)

    builder.add_edge(START, "query_understanding")

    # Either stop and ask the user for their state, or go and search.
    builder.add_conditional_edges(
        "query_understanding",
        route_after_understanding,
        {
            "clarify": END,
            "retrieve": "retrieval",
        },
    )

    builder.add_edge("retrieval", "synthesis")
    builder.add_edge("synthesis", "verification")

    # Loop back to synthesis when a citation could not be grounded.
    builder.add_conditional_edges(
        "verification",
        route_after_verification,
        {
            "retry": "increment_retry",
            "done": END,
        },
    )
    builder.add_edge("increment_retry", "synthesis")

    compiled = builder.compile()
    logger.info(
        "Orchestration graph compiled (retriever=%s, synthesizer=%s)",
        "real" if retriever else "STUB",
        "real" if synthesizer else "STUB",
    )
    return compiled


def describe_graph() -> str:
    """Return a Mermaid diagram of the graph, for the README and the report.

    Mermaid is used rather than ASCII because GitHub renders it directly in
    markdown, and because LangGraph produces it without any extra dependency.
    """
    return build_graph().get_graph().draw_mermaid()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(describe_graph())

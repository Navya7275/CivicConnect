"""Tests for the orchestration graph.

Covers the two pieces of routing that make this a state machine rather than a
straight line: the clarification exit, and the verification retry loop.

Fake retrievers and synthesizers are used throughout, so nothing here touches
the network or needs an API key.
"""

from __future__ import annotations

from typing import Any

from backend.orchestration.graph import build_graph
from backend.orchestration.state import MAX_RETRIES, initial_state


# --------------------------------------------------------------------------
# Test doubles
# --------------------------------------------------------------------------

REAL_CHUNK: dict[str, Any] = {
    "chunk_id": "cpa2019-s35",
    "text": "A complaint may be filed with the District Commission...",
    "act": "Consumer Protection Act, 2019",
    "chapter": "Chapter IV",
    "section": "Section 35",
    "jurisdiction": "Central",
    "effective_date": "2020-07-20",
    "source_url": "https://indiacode.nic.in/show-data?sectionId=64353",
}


class FakeRetriever:
    """Returns a fixed chunk and records how it was called."""

    def __init__(self, chunks: list[dict[str, Any]] | None = None) -> None:
        self.chunks = chunks if chunks is not None else [REAL_CHUNK]
        self.calls: list[dict[str, Any]] = []

    def search(self, query: str, filters=None, limit: int = 5):
        self.calls.append({"query": query, "filters": filters, "limit": limit})
        return self.chunks


class GroundedSynthesizer:
    """Cites only what it was given. Should always verify."""

    def __init__(self) -> None:
        self.call_count = 0

    def synthesize(self, query: str, retrieved_chunks):
        self.call_count += 1
        return {
            "answer": "You may file a complaint with the District Commission.",
            "citations": [
                {
                    "act": chunk["act"],
                    "section": chunk["section"],
                    "jurisdiction": chunk["jurisdiction"],
                    "source_url": chunk["source_url"],
                    "chunk_id": chunk["chunk_id"],
                }
                for chunk in retrieved_chunks
            ],
        }


class HallucinatingSynthesizer:
    """Cites a section that was never retrieved. Should always fail verification.

    This is the failure the whole project exists to catch.
    """

    def __init__(self) -> None:
        self.call_count = 0

    def synthesize(self, query: str, retrieved_chunks):
        self.call_count += 1
        return {
            "answer": "Under Section 999 you are entitled to triple damages.",
            "citations": [
                {
                    "act": "Consumer Protection Act, 2019",
                    "section": "Section 999",       # does not exist
                    "jurisdiction": "Central",
                    "source_url": "https://indiacode.nic.in/invented",
                    "chunk_id": "does-not-exist",
                }
            ],
        }


class LegacyKeySynthesizer:
    """Returns 'sources' instead of 'citations', as the agent did before PR #6."""

    def synthesize(self, query: str, retrieved_chunks):
        return {
            "answer": "An answer.",
            "sources": [
                {
                    "act": chunk["act"],
                    "section": chunk["section"],
                    "jurisdiction": chunk["jurisdiction"],
                    "source_url": chunk["source_url"],
                    "chunk_id": chunk["chunk_id"],
                }
                for chunk in retrieved_chunks
            ],
        }


# --------------------------------------------------------------------------
# The happy path
# --------------------------------------------------------------------------

def test_query_flows_through_every_node() -> None:
    """PHASES.md C1 'done when': a real query reaches the end of the graph."""
    graph = build_graph(retriever=FakeRetriever(), synthesizer=GroundedSynthesizer())

    final = graph.invoke(initial_state("The seller refused a refund for a defective product"))

    assert final["intent"] == "consumer"
    assert final["jurisdiction"] == "Central"
    assert final["retrieved_chunks"], "retrieval node did not run"
    assert final["draft_answer"], "synthesis node did not run"
    assert final["verification_status"] == "verified"
    assert final["verified"] is True


def test_grounded_answer_is_marked_verified() -> None:
    graph = build_graph(retriever=FakeRetriever(), synthesizer=GroundedSynthesizer())
    final = graph.invoke(initial_state("How do I complain about a faulty product?"))

    assert final["verified"] is True
    assert len(final["citations"]) == 1
    assert final["citations"][0]["section"] == "Section 35"


def test_retrieval_receives_the_rewritten_query_and_jurisdiction() -> None:
    retriever = FakeRetriever()
    graph = build_graph(retriever=retriever, synthesizer=GroundedSynthesizer())

    graph.invoke(initial_state("refund for a defective product"))

    assert len(retriever.calls) == 1
    assert retriever.calls[0]["filters"] == {"jurisdiction": "Central"}


def test_synthesizer_returning_sources_still_works() -> None:
    """Tolerate the old key name, for any agent predating issue #2 item B6."""
    graph = build_graph(retriever=FakeRetriever(), synthesizer=LegacyKeySynthesizer())
    final = graph.invoke(initial_state("refund for a defective product"))

    assert len(final["citations"]) == 1
    assert final["verified"] is True


# --------------------------------------------------------------------------
# The clarification exit
# --------------------------------------------------------------------------

def test_state_specific_question_stops_before_retrieval() -> None:
    """PHASES.md C1 'done when': asks for the state instead of guessing.

    Importantly it must not search at all — searching with the wrong
    jurisdiction would waste work and could surface another state's law.
    """
    retriever = FakeRetriever()
    graph = build_graph(retriever=retriever, synthesizer=GroundedSynthesizer())

    final = graph.invoke(initial_state("Can my landlord evict me without notice?"))

    assert final["needs_clarification"] is True
    assert final["clarification_question"] is not None
    assert retriever.calls == [], "retrieval ran even though we needed clarification"
    assert final["retrieved_chunks"] == []
    assert final["draft_answer"] == ""


def test_same_question_with_a_state_goes_all_the_way_through() -> None:
    retriever = FakeRetriever()
    graph = build_graph(retriever=retriever, synthesizer=GroundedSynthesizer())

    final = graph.invoke(
        initial_state("Can my landlord evict me without notice?", state="Madhya Pradesh")
    )

    assert final["needs_clarification"] is False
    assert final["jurisdiction"] == "Madhya Pradesh"
    assert len(retriever.calls) == 1
    assert retriever.calls[0]["filters"] == {"jurisdiction": "Madhya Pradesh"}


# --------------------------------------------------------------------------
# The verification retry loop
# --------------------------------------------------------------------------

def test_invented_citation_is_caught_and_not_marked_verified() -> None:
    """An answer citing a section we never retrieved must never come back verified."""
    graph = build_graph(retriever=FakeRetriever(), synthesizer=HallucinatingSynthesizer())

    final = graph.invoke(initial_state("What compensation can I claim?"))

    assert final["verified"] is False
    assert final["verification_status"] == "ungrounded"


def test_ungrounded_answer_triggers_retries_then_stops() -> None:
    """The loop must be bounded. Two retries, then give up — never spin forever."""
    synthesizer = HallucinatingSynthesizer()
    graph = build_graph(retriever=FakeRetriever(), synthesizer=synthesizer)

    final = graph.invoke(initial_state("What compensation can I claim?"))

    assert final["retry_count"] == MAX_RETRIES
    # One first attempt plus MAX_RETRIES retries.
    assert synthesizer.call_count == MAX_RETRIES + 1
    assert final["verified"] is False


def test_grounded_answer_does_not_retry() -> None:
    synthesizer = GroundedSynthesizer()
    graph = build_graph(retriever=FakeRetriever(), synthesizer=synthesizer)

    final = graph.invoke(initial_state("refund for a defective product"))

    assert synthesizer.call_count == 1
    assert final["retry_count"] == 0


def test_no_chunks_means_no_citations_and_not_verified() -> None:
    """'We don't have enough information' is a valid answer, but never a verified one."""
    graph = build_graph(retriever=FakeRetriever(chunks=[]), synthesizer=GroundedSynthesizer())

    final = graph.invoke(initial_state("refund for a defective product"))

    assert final["citations"] == []
    assert final["verified"] is False
    assert final["verification_status"] == "skipped"


# --------------------------------------------------------------------------
# The stub defaults
# --------------------------------------------------------------------------

def test_graph_builds_and_runs_with_no_arguments() -> None:
    """The Phase C1 default must work without a database, index or API key."""
    graph = build_graph()
    final = graph.invoke(initial_state("refund for a defective product"))

    assert final["draft_answer"], "stub graph produced no answer"
    assert final["intent"] == "consumer"


def test_stub_citations_are_obviously_fake() -> None:
    """Placeholder data must never be mistakable for a real citation.

    `example.invalid` is a reserved domain that cannot resolve, so a stub
    citation leaking into the UI fails loudly instead of looking plausible.
    """
    graph = build_graph()
    final = graph.invoke(initial_state("refund for a defective product"))

    for citation in final["citations"]:
        assert "STUB" in citation["act"]
        assert "example.invalid" in citation["source_url"]

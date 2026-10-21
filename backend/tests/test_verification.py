"""Tests for the Verification agent (Phase C3).

The test that matters most here is
`test_invented_section_in_prose_is_caught_even_with_clean_citations`. It
describes the hole Phase C1 had: a synthesis agent can return a tidy citations
list while writing a section number into the prose that nothing supports. The
old check compared only the citations list, so that answer came back verified
and the user read an unverified section number.

Everything runs offline.
"""

from __future__ import annotations

from typing import Any

import pytest

from backend.agents.verification import (
    VerificationAgent,
    extract_section_numbers,
    normalise_section,
)
from backend.orchestration.graph import build_graph
from backend.orchestration.state import MAX_RETRIES, initial_state


# --------------------------------------------------------------------------
# Section extraction
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Under Section 35 you may file a complaint.", ["35"]),
        ("See Sections 35 and 36 of the Act.", ["35", "36"]),
        ("Sections 35, 36 and 38 apply.", ["35", "36", "38"]),
        ("Section 2(9) defines consumer rights.", ["2"]),          # sub-clause -> parent
        ("Section 35(1)(a) is relevant.", ["35"]),
        ("Refer to sec. 69 for the limitation period.", ["69"]),
        ("See §47 of the Act.", ["47"]),
        ("As per s. 138 of the NI Act", ["138"]),
        ("Section 35A was inserted later.", ["35A"]),
        ("Under Section 35 you may complain; appeals go to Section 41.", ["35", "41"]),
    ],
)
def test_extracts_section_references(text: str, expected: list[str]) -> None:
    assert extract_section_numbers(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "You must file within thirty days.",
        "A claim of Rs 50,00,000 or less goes to the District Commission.",
        "The limitation period is 2 years.",
        "This applies to all consumers.",
        "Chapter IV covers complaints.",
    ],
)
def test_ordinary_numbers_are_not_mistaken_for_sections(text: str) -> None:
    """An anchor word is required, so dates, amounts and durations are ignored.

    Matching bare numbers would make every answer look like it cited something.
    """
    assert extract_section_numbers(text) == []


def test_duplicate_references_are_collapsed() -> None:
    assert extract_section_numbers("Section 35 ... later, Section 35 again") == ["35"]


def test_empty_text_yields_nothing() -> None:
    assert extract_section_numbers("") == []
    assert extract_section_numbers(None) == []  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("stored", "expected"),
    [
        ("Section 35", "35"),
        ("Section 2(9)", "2"),
        ("35A", "35A"),
        ("Chapter IV", None),      # no number -> never matched against
        (None, None),
        ("", None),
    ],
)
def test_normalise_section(stored: str | None, expected: str | None) -> None:
    assert normalise_section(stored) == expected


# --------------------------------------------------------------------------
# The agent
# --------------------------------------------------------------------------

CHUNK_35: dict[str, Any] = {
    "chunk_id": "cpa2019-s35",
    "act": "Consumer Protection Act, 2019",
    "section": "Section 35",
    "jurisdiction": "Central",
    "source_url": "https://indiacode.nic.in/show-data?sectionId=64353",
}

CITATION_35: dict[str, Any] = {
    "act": "Consumer Protection Act, 2019",
    "section": "Section 35",
    "jurisdiction": "Central",
    "source_url": "https://indiacode.nic.in/show-data?sectionId=64353",
    "chunk_id": "cpa2019-s35",
}


@pytest.fixture
def agent() -> VerificationAgent:
    return VerificationAgent()


def test_grounded_answer_verifies(agent) -> None:
    result = agent.verify(
        answer="Under Section 35 you may file a complaint with the District Commission.",
        citations=[CITATION_35],
        retrieved_chunks=[CHUNK_35],
    )
    assert result.verified is True
    assert result.status == "verified"
    assert result.hallucinated_sections == []
    assert result.checked_sections == ["35"]


def test_invented_section_in_prose_is_caught_even_with_clean_citations(agent) -> None:
    """The Phase C1 hole, closed.

    The citations list contains only Section 35, which was retrieved, so the
    old metadata-only check passed. But the prose claims Section 47, which was
    never retrieved — and that is the number the user actually reads.
    """
    result = agent.verify(
        answer="Under Section 47 you may appeal to the State Commission.",
        citations=[CITATION_35],        # clean
        retrieved_chunks=[CHUNK_35],
    )

    assert result.verified is False
    assert result.status == "ungrounded"
    assert result.hallucinated_sections == ["47"]
    assert result.ungrounded_citations == []   # the list really was fine
    assert "47" in result.rejection_summary


def test_ungrounded_citation_is_still_caught(agent) -> None:
    """The original check must keep working alongside the new one."""
    result = agent.verify(
        answer="You may file a complaint.",        # no section in the prose
        citations=[
            {
                "act": "Consumer Protection Act, 2019",
                "section": "Section 999",
                "jurisdiction": "Central",
                "source_url": "https://indiacode.nic.in/invented",
                "chunk_id": "does-not-exist",
            }
        ],
        retrieved_chunks=[CHUNK_35],
    )
    assert result.verified is False
    assert len(result.ungrounded_citations) == 1
    assert "Section 999" in result.rejection_summary


def test_both_failures_are_reported_together(agent) -> None:
    result = agent.verify(
        answer="Section 47 and Section 88 apply.",
        citations=[{"act": "Made Up Act", "section": "Section 999", "chunk_id": "nope"}],
        retrieved_chunks=[CHUNK_35],
    )
    assert result.hallucinated_sections == ["47", "88"]
    assert len(result.ungrounded_citations) == 1


def test_subclause_reference_grounds_against_its_parent_section(agent) -> None:
    """Our corpus stores section-level chunks, so Section 2(9) needs Section 2."""
    chunk_2 = {**CHUNK_35, "chunk_id": "cpa2019-s2-9", "section": "Section 2"}
    result = agent.verify(
        answer="Section 2(9) sets out your consumer rights.",
        citations=[{**CITATION_35, "chunk_id": "cpa2019-s2-9", "section": "Section 2"}],
        retrieved_chunks=[chunk_2],
    )
    assert result.verified is True


def test_no_citations_and_no_sections_is_skipped_not_failed(agent) -> None:
    """'We don't have enough information' is legitimate, but never 'verified'."""
    result = agent.verify(
        answer="The available sources do not contain enough information to answer this.",
        citations=[],
        retrieved_chunks=[],
    )
    assert result.status == "skipped"
    assert result.verified is False


def test_prose_claiming_a_section_with_no_citations_at_all_fails(agent) -> None:
    """An answer that cites nothing but names a section is not trustworthy."""
    result = agent.verify(
        answer="Section 420 of the Act covers this.",
        citations=[],
        retrieved_chunks=[CHUNK_35],
    )
    assert result.verified is False
    assert result.hallucinated_sections == ["420"]


# --------------------------------------------------------------------------
# Through the graph
# --------------------------------------------------------------------------

class CleanListDirtyProseSynthesizer:
    """Returns a tidy citations list while inventing a section in the prose.

    This is the adversary the C1 verification node could not catch.
    """

    def __init__(self) -> None:
        self.call_count = 0

    def synthesize(self, query: str, retrieved_chunks):
        self.call_count += 1
        return {
            "answer": "Under Section 47 you are entitled to triple damages.",
            "citations": [
                {
                    "act": c["act"],
                    "section": c["section"],
                    "jurisdiction": c["jurisdiction"],
                    "source_url": c["source_url"],
                    "chunk_id": c["chunk_id"],
                }
                for c in retrieved_chunks
            ],
        }


class HonestSynthesizer:
    def synthesize(self, query: str, retrieved_chunks):
        return {
            "answer": "Under Section 35 you may file a complaint with the District Commission.",
            "citations": [
                {
                    "act": c["act"],
                    "section": c["section"],
                    "jurisdiction": c["jurisdiction"],
                    "source_url": c["source_url"],
                    "chunk_id": c["chunk_id"],
                }
                for c in retrieved_chunks
            ],
        }


class FixedRetriever:
    def search(self, query: str, filters=None, limit: int = 5):
        return [CHUNK_35]


def test_graph_catches_prose_hallucination_and_retries() -> None:
    """End to end: the answer is rejected, retried, and never marked verified."""
    synthesizer = CleanListDirtyProseSynthesizer()
    graph = build_graph(retriever=FixedRetriever(), synthesizer=synthesizer)

    final = graph.invoke(initial_state("What compensation can I claim?"))

    assert final["verified"] is False
    assert final["verification_status"] == "ungrounded"
    assert final["hallucinated_sections"] == ["47"]
    assert final["retry_count"] == MAX_RETRIES
    assert synthesizer.call_count == MAX_RETRIES + 1


def test_graph_verifies_an_honest_answer() -> None:
    graph = build_graph(retriever=FixedRetriever(), synthesizer=HonestSynthesizer())

    final = graph.invoke(initial_state("How do I complain about a faulty product?"))

    assert final["verified"] is True
    assert final["hallucinated_sections"] == []
    assert final["checked_sections"] == ["35"]
    assert final["retry_count"] == 0

"""Tests for the Phase C2 provider wiring.

Two things need proving here, and they pull in opposite directions:

1. When the real components are missing, the API still starts, serves stub
   answers, and says clearly on `/health` what is unavailable and why.
2. When they *are* present, they get used — the fallbacks stop applying.

The second is the one worth testing hardest, because it is the thing that
silently fails. A graceful fallback that never stops falling back is just a
permanent stub with extra steps.

Everything here is offline: the real components are simulated with fakes and
monkeypatched imports.
"""

from __future__ import annotations

import sys
import types
from typing import Any

import pytest
from fastapi.testclient import TestClient

from backend.orchestration import providers


# --------------------------------------------------------------------------
# Fallback behaviour — nothing available
# --------------------------------------------------------------------------

def test_retriever_reports_why_it_is_unavailable(monkeypatch) -> None:
    """A missing retrieval package must produce a readable reason, not a crash."""
    monkeypatch.delitem(sys.modules, "backend.retrieval.hybrid_search", raising=False)

    retriever, status = providers.load_retriever()

    # On current main the retrieval package uses bare imports and cannot be
    # imported from the repo root, so this is the real situation today.
    if retriever is None:
        assert status.startswith("unavailable:")
        assert status != "unavailable:"  # must actually say something


def test_synthesizer_unavailable_without_an_api_key(monkeypatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    synthesizer, status = providers.load_synthesizer()

    assert synthesizer is None
    assert "GROQ_API_KEY" in status


def test_load_all_never_raises(monkeypatch) -> None:
    """Startup must not be able to fail because a teammate's layer is missing."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    retriever, synthesizer, query_logger, status = providers.load_all()

    assert isinstance(status.retrieval, str) and status.retrieval
    assert isinstance(status.synthesis, str) and status.synthesis
    assert isinstance(status.query_logging, str) and status.query_logging


def test_fully_real_is_false_when_anything_is_missing() -> None:
    status = providers.ProviderStatus(
        retrieval=providers.STATUS_REAL,
        synthesis="unavailable: GROQ_API_KEY is not set",
        query_logging="unavailable: data layer not importable",
    )
    assert status.fully_real is False


def test_fully_real_ignores_query_logging() -> None:
    """Query logging is useful but not required for a real answer."""
    status = providers.ProviderStatus(
        retrieval=providers.STATUS_REAL,
        synthesis=providers.STATUS_REAL,
        query_logging="unavailable: data layer not importable",
    )
    assert status.fully_real is True


# --------------------------------------------------------------------------
# Health reporting
# --------------------------------------------------------------------------

def test_health_reports_provider_status() -> None:
    from backend.main import app

    with TestClient(app) as client:
        body = client.get("/health").json()

    assert body["status"] == "ok"
    assert body["graph_ready"] is True
    # Present and informative whichever way they resolved.
    for key in ("retrieval", "synthesis", "query_logging"):
        assert isinstance(body[key], str) and body[key]
    assert isinstance(body["serving_real_answers"], bool)


def test_health_says_stub_answers_when_components_are_missing(monkeypatch) -> None:
    """The demo-day protection: you can always tell if answers are fake."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setattr(
        providers, "load_retriever", lambda: (None, "unavailable: index artifacts missing")
    )

    import backend.main as main_module

    with TestClient(main_module.app) as client:
        body = client.get("/health").json()

    assert body["serving_real_answers"] is False
    assert "unavailable" in body["retrieval"]


# --------------------------------------------------------------------------
# The real path — proving the fallback actually stops applying
# --------------------------------------------------------------------------

REAL_CHUNK: dict[str, Any] = {
    "chunk_id": "cpa2019-s35",
    "text": "A complaint may be filed with the District Commission.",
    "act": "Consumer Protection Act, 2019",
    "chapter": "Chapter IV",
    "section": "Section 35",
    "jurisdiction": "Central",
    "effective_date": "2020-07-20",
    "source_url": "https://indiacode.nic.in/show-data?sectionId=64353",
}


class FakeHybridRetriever:
    """Stands in for Ayushi's HybridRetriever once PR #6 lands."""

    def __init__(self, chunks=None) -> None:
        self.calls: list[dict[str, Any]] = []

    def search(self, query: str, filters=None, limit: int = 5):
        self.calls.append({"query": query, "filters": filters})
        return [REAL_CHUNK]


class FakeSynthesisAgent:
    """Stands in for the real Groq-backed agent."""

    def synthesize(self, query: str, retrieved_chunks):
        return {
            "answer": "You may file a complaint with the District Commission under Section 35.",
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


@pytest.fixture
def real_components(monkeypatch):
    """Install fake 'real' components the way the loaders expect to find them."""
    retrieval_mod = types.ModuleType("backend.retrieval.hybrid_search")
    retrieval_mod.HybridRetriever = FakeHybridRetriever
    monkeypatch.setitem(sys.modules, "backend.retrieval.hybrid_search", retrieval_mod)

    synthesis_mod = types.ModuleType("backend.agents.synthesis")
    synthesis_mod.SynthesisAgent = FakeSynthesisAgent
    monkeypatch.setitem(sys.modules, "backend.agents.synthesis", synthesis_mod)

    monkeypatch.setenv("GROQ_API_KEY", "test-key-not-a-real-one")


def test_real_components_are_picked_up_when_available(real_components) -> None:
    retriever, retrieval_status = providers.load_retriever()
    synthesizer, synthesis_status = providers.load_synthesizer()

    assert retrieval_status == providers.STATUS_REAL
    assert synthesis_status == providers.STATUS_REAL
    assert isinstance(retriever, FakeHybridRetriever)
    assert isinstance(synthesizer, FakeSynthesisAgent)


def test_query_returns_a_real_grounded_answer(real_components) -> None:
    """PHASES.md C2 'done when': /query returns a real answer, not a mock.

    This is the test that will confirm C2 the moment #6 merges — the only thing
    standing in for reality here is the two fakes above.
    """
    import backend.main as main_module

    with TestClient(main_module.app) as client:
        health = client.get("/health").json()
        body = client.post(
            "/query", json={"query": "The seller refused a refund for a defective phone"}
        ).json()

    assert health["serving_real_answers"] is True

    # No stub markers anywhere in the response.
    assert "STUB" not in body["answer"]
    assert body["answer"].startswith("You may file a complaint")
    assert body["verified"] is True
    assert len(body["citations"]) == 1

    citation = body["citations"][0]
    assert citation["act"] == "Consumer Protection Act, 2019"
    assert citation["section"] == "Section 35"
    assert "example.invalid" not in citation["source_url"]


def test_clarification_still_short_circuits_with_real_components(real_components) -> None:
    """A state-specific question must not reach the real retriever either."""
    import backend.main as main_module

    with TestClient(main_module.app) as client:
        body = client.post(
            "/query", json={"query": "Can my landlord evict me without notice?"}
        ).json()

    assert body["needs_clarification"] is True
    assert body["citations"] == []


# --------------------------------------------------------------------------
# Query logging (C2.3)
# --------------------------------------------------------------------------

def test_query_log_receives_the_answer_and_cited_ids(real_components, monkeypatch) -> None:
    recorded: list[dict[str, Any]] = []

    monkeypatch.setattr(
        providers,
        "load_query_logger",
        lambda: (lambda **kwargs: recorded.append(kwargs), providers.STATUS_REAL),
    )

    import backend.main as main_module

    with TestClient(main_module.app) as client:
        client.post("/query", json={"query": "The seller refused a refund", "state": None})

    assert len(recorded) == 1
    entry = recorded[0]
    assert entry["query"] == "The seller refused a refund"
    assert entry["cited_chunk_ids"] == ["cpa2019-s35"]
    assert entry["verified"] is True


def test_clarification_is_not_logged_as_an_answer(real_components, monkeypatch) -> None:
    """Asking the user for their state is not an answer, so it is not logged."""
    recorded: list[dict[str, Any]] = []
    monkeypatch.setattr(
        providers,
        "load_query_logger",
        lambda: (lambda **kwargs: recorded.append(kwargs), providers.STATUS_REAL),
    )

    import backend.main as main_module

    with TestClient(main_module.app) as client:
        client.post("/query", json={"query": "Can my landlord evict me without notice?"})

    assert recorded == []


def test_a_logging_failure_does_not_break_the_response(real_components, monkeypatch) -> None:
    """A broken log write must never turn a good answer into a 500."""
    def exploding_logger(**kwargs):
        raise RuntimeError("database is on fire")

    monkeypatch.setattr(
        providers, "load_query_logger", lambda: (exploding_logger, providers.STATUS_REAL)
    )

    import backend.main as main_module

    with TestClient(main_module.app) as client:
        response = client.post("/query", json={"query": "The seller refused a refund"})

    assert response.status_code == 200, "a query-logging failure must not fail the request"
    assert "District Commission" in response.json()["answer"]

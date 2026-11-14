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


# --------------------------------------------------------------------------
# Retrieval score passthrough (issue #12's hybrid breakdown table)
# --------------------------------------------------------------------------

class ScoringSynthesizer:
    """Mimics the real agent: carries the retriever diagnostics into citations."""

    def synthesize(self, query: str, retrieved_chunks):
        return {
            "answer": "You may file a complaint with the District Commission.",
            "citations": [
                {
                    "act": c["act"],
                    "section": c["section"],
                    "jurisdiction": c["jurisdiction"],
                    "source_url": c["source_url"],
                    "chunk_id": c["chunk_id"],
                    "_retrieval_scores": c.get("_retrieval_scores"),
                    "_rrf_score": c.get("_rrf_score"),
                }
                for c in retrieved_chunks
            ],
        }


class ScoringRetriever:
    """Returns a chunk tagged the way the hybrid retriever tags them."""

    def search(self, query: str, filters=None, limit: int = 5):
        return [
            {
                **REAL_CHUNK,
                "_retrieval_scores": {"dense": 0.884, "bm25": 7.412},
                "_rrf_score": 0.03279,
                "_retriever": "dense",
            }
        ]


@pytest.fixture
def scoring_components(monkeypatch):
    retrieval_mod = types.ModuleType("backend.retrieval.hybrid_search")
    retrieval_mod.HybridRetriever = ScoringRetriever
    monkeypatch.setitem(sys.modules, "backend.retrieval.hybrid_search", retrieval_mod)

    synthesis_mod = types.ModuleType("backend.agents.synthesis")
    synthesis_mod.SynthesisAgent = ScoringSynthesizer
    monkeypatch.setitem(sys.modules, "backend.agents.synthesis", synthesis_mod)

    monkeypatch.setenv("GROQ_API_KEY", "test-key-not-a-real-one")


def test_retrieval_scores_reach_the_api_response(scoring_components) -> None:
    """The scores must survive synthesis, the schema and the route.

    They used to be dropped at every one of those three steps, which meant the
    UI's hybrid breakdown table could never render -- it gated on a field the
    backend never sent. This asserts the whole path, not just one hop.
    """
    import backend.main as main_module

    with TestClient(main_module.app) as client:
        body = client.post("/query", json={"query": "The seller refused a refund"}).json()

    citation = body["citations"][0]
    assert "retrieval_scores" in citation, "scores were dropped before the response"

    scores = citation["retrieval_scores"]
    assert scores["dense"] == pytest.approx(0.884)
    assert scores["bm25"] == pytest.approx(7.412)
    assert scores["rrf"] == pytest.approx(0.03279)


def test_citations_without_scores_report_none(real_components) -> None:
    """A citation from a non-hybrid path must not invent scores.

    The frontend gates its table on this field, so it has to be absent rather
    than zero-filled when nothing measured the chunk.
    """
    import backend.main as main_module

    with TestClient(main_module.app) as client:
        body = client.post("/query", json={"query": "The seller refused a refund"}).json()

    assert body["citations"][0]["retrieval_scores"] is None


def test_stub_citations_carry_no_scores(monkeypatch) -> None:
    """Phase C1 stubs have nothing to score, so the table stays hidden.

    The stub path has to be forced. This test used to take no fixture at all,
    which meant it tested whatever the machine happened to load: stubs on a
    clone with no index built, the real hybrid retriever on a working install.
    So it passed only where retrieval was broken and failed once the project
    started working -- the assertion was backwards on exactly the installs we
    care about.

    Forcing the stub the way the rest of this file does makes it a real test of
    the stub contract: no scores invented when nothing measured the chunk.
    """
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setattr(
        providers, "load_retriever", lambda: (None, "unavailable: index artifacts missing")
    )

    import backend.main as main_module

    with TestClient(main_module.app) as client:
        body = client.post("/query", json={"query": "The seller refused a refund"}).json()

    # Guard the premise: if this ever loads real components the assertion below
    # would pass for the wrong reason, and we would be back to a test that goes
    # green when the pipeline breaks.
    with TestClient(main_module.app) as client:
        assert client.get("/health").json()["serving_real_answers"] is False

    assert body["citations"], "the stub path should still return citations"
    for citation in body["citations"]:
        assert citation.get("retrieval_scores") is None

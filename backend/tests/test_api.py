"""Tests for the HTTP layer.

Checks that the API returns exactly the shape agreed in
`docs/PROJECT_PLAN.md` section 3 — because the frontend binds to these field
names, and a mismatch fails silently in JavaScript rather than raising.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    """A test client. The `with` block triggers startup, which builds the graph."""
    with TestClient(app) as test_client:
        yield test_client


# --------------------------------------------------------------------------
# Health
# --------------------------------------------------------------------------

def test_health_reports_ok(client) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["graph_ready"] is True


def test_root_points_at_the_docs(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["docs"] == "/docs"


# --------------------------------------------------------------------------
# The response contract
# --------------------------------------------------------------------------

def test_query_returns_every_contract_field(client) -> None:
    """PROJECT_PLAN section 3 — all five keys, every time."""
    response = client.post("/query", json={"query": "The seller refused a refund", "state": None})

    assert response.status_code == 200
    body = response.json()

    assert set(body) == {"answer", "citations", "jurisdiction", "verified", "needs_clarification"}
    assert isinstance(body["answer"], str)
    assert isinstance(body["citations"], list)
    assert isinstance(body["jurisdiction"], str)
    assert isinstance(body["verified"], bool)
    assert isinstance(body["needs_clarification"], bool)


def test_citations_use_the_agreed_field_names(client) -> None:
    """act / section / jurisdiction / source_url — not actName or sectionNumber.

    Issue #3 tracks the frontend side of this. This test guards the backend side
    so the two cannot drift apart again without something going red.
    """
    response = client.post("/query", json={"query": "The seller refused a refund"})
    citations = response.json()["citations"]

    assert citations, "expected at least one citation from the stub"
    for citation in citations:
        assert {"act", "section", "jurisdiction", "source_url"} <= set(citation)


def test_state_specific_question_returns_a_clarification(client) -> None:
    """The clarification path must still return a valid, complete response."""
    response = client.post("/query", json={"query": "Can my landlord evict me without notice?"})

    assert response.status_code == 200
    body = response.json()

    assert body["needs_clarification"] is True
    assert body["citations"] == []
    assert body["verified"] is False
    assert "state" in body["answer"].lower()


def test_supplying_a_state_removes_the_clarification(client) -> None:
    response = client.post(
        "/query",
        json={"query": "Can my landlord evict me without notice?", "state": "Kerala"},
    )
    body = response.json()

    assert body["needs_clarification"] is False
    assert body["jurisdiction"] == "Kerala"


# --------------------------------------------------------------------------
# Input validation
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "payload",
    [
        {},                          # missing query
        {"query": ""},               # empty
        {"query": "   "},            # whitespace only
        {"query": "ab"},             # below the minimum length
        {"query": "x" * 2001},       # above the maximum length
    ],
)
def test_bad_input_is_rejected_with_422(client, payload) -> None:
    response = client.post("/query", json=payload)
    assert response.status_code == 422


def test_query_is_trimmed_before_use(client) -> None:
    response = client.post("/query", json={"query": "   The seller refused a refund   "})
    assert response.status_code == 200


def test_empty_state_is_treated_as_no_state(client) -> None:
    """An unselected dropdown often sends "" rather than null. Treat them the same."""
    response = client.post(
        "/query",
        json={"query": "Can my landlord evict me without notice?", "state": ""},
    )
    assert response.json()["needs_clarification"] is True

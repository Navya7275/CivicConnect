"""Pydantic models for the CivicConnect API.

This module is the machine-readable version of the API contract in
`docs/PROJECT_PLAN.md` section 3. If there is ever a disagreement about what
shape the API returns, this file is the answer.

Do not change a field name here without telling the whole team first — the
frontend binds to these names, and a silent rename breaks it without raising
an error anywhere.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class RetrievalScores(BaseModel):
    """How each retriever scored the chunk behind a citation.

    These exist to make hybrid retrieval inspectable rather than a claim: the
    UI shows them per citation, and Phase E uses them to compare dense-only
    against hybrid. All optional — a citation from a non-hybrid path (or the
    Phase C1 stub) simply has none.
    """

    dense: float | None = Field(None, description="Cosine similarity from the FAISS index")
    bm25: float | None = Field(None, description="BM25 relevance score")
    rrf: float | None = Field(None, description="Fused Reciprocal Rank Fusion score")


class Citation(BaseModel):
    """One statutory source backing part of an answer.

    The first four fields are the agreed contract. `chunk_id`, `excerpt` and
    `retrieval_scores` are optional extras: the retrieval layer may supply
    them, and the verification agent uses `chunk_id` to check groundedness,
    but the frontend must not depend on them being present.
    """

    act: str = Field(..., description="Name of the Act or scheme, e.g. 'Consumer Protection Act, 2019'")
    section: str = Field(..., description="Section reference, e.g. 'Section 35'")
    jurisdiction: str = Field(..., description="'Central' or a state name, e.g. 'Madhya Pradesh'")
    source_url: str = Field(..., description="Link to the specific section on the source site")

    chunk_id: str | None = Field(None, description="Internal chunk identifier, used for verification")
    excerpt: str | None = Field(None, description="The exact quoted text this citation refers to")
    retrieval_scores: RetrievalScores | None = Field(
        None, description="Per-retriever scores, when the hybrid retriever supplied them"
    )


class QueryRequest(BaseModel):
    """Request body for `POST /query`."""

    query: str = Field(..., min_length=3, max_length=2000, description="The user's question in plain language")
    state: str | None = Field(None, max_length=100, description="Indian state or UT, if the user has chosen one")

    @field_validator("query")
    @classmethod
    def _query_not_blank(cls, value: str) -> str:
        """Reject a query that is only whitespace, and trim the edges."""
        cleaned = value.strip()
        if len(cleaned) < 3:
            raise ValueError("query must contain at least 3 non-whitespace characters")
        return cleaned

    @field_validator("state")
    @classmethod
    def _normalise_state(cls, value: str | None) -> str | None:
        """Treat an empty string the same as no state at all."""
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class QueryResponse(BaseModel):
    """Response body for `POST /query`.

    Matches `docs/PROJECT_PLAN.md` section 3 exactly.

    Note that `verified` describes the whole answer, not individual citations.
    The verification agent checks every cited section against the retrieved
    sources and returns one verdict for the response.
    """

    answer: str = Field(..., description="The plain-language answer, or the clarification question")
    citations: list[Citation] = Field(default_factory=list, description="Sources backing the answer")
    jurisdiction: str = Field(..., description="Which body of law this answer was drawn from")
    verified: bool = Field(..., description="True when every cited section was found in the retrieved sources")
    needs_clarification: bool = Field(..., description="True when we need the user's state before answering")


class HealthResponse(BaseModel):
    """Response body for `GET /health`."""

    status: str = Field(..., description="'ok' when the service is up")
    version: str = Field(..., description="Application version")
    graph_ready: bool = Field(..., description="True when the orchestration graph compiled successfully")

    # Phase C2 diagnostics. These say whether /query is serving real grounded
    # answers or stub data, and when something is missing, what. Optional so
    # the frontend never has to depend on them.
    retrieval: str | None = Field(None, description="'real', or why the real retriever is unavailable")
    synthesis: str | None = Field(None, description="'real', or why the real synthesis agent is unavailable")
    query_logging: str | None = Field(None, description="'real', or why query logging is unavailable")
    serving_real_answers: bool | None = Field(
        None,
        description="True only when both retrieval and synthesis are the real implementations",
    )

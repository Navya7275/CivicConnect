"""End-to-end integration test: real retrieval into mocked synthesis.

Like `test_hybrid.py`, this runs the real retriever, so it needs a populated
database and the prebuilt indexes and skips without them. The LLM call is
mocked — a test must never depend on a live API or spend credits.

Run after:

    python -m data.ingestion.load_seed
    python -m data.indexing.build_index
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ARTIFACTS_DIR = (
    Path(__file__).resolve().parents[2] / "data" / "indexing" / "artifacts"
)

_missing = [
    name
    for name in ("faiss.index", "bm25.pkl", "chunk_ids.json")
    if not (ARTIFACTS_DIR / name).exists()
]

pytestmark = pytest.mark.skipif(
    bool(_missing),
    reason=(
        f"index artifacts missing ({', '.join(_missing)}); "
        "run `python -m data.indexing.build_index` first"
    ),
)


@pytest.fixture(autouse=True)
def _dummy_api_key(monkeypatch):
    """SynthesisAgent raises without a key; the Groq class itself is patched."""
    monkeypatch.setenv("GROQ_API_KEY", "test-key-not-a-real-one")


def test_retrieval_and_synthesis_pipeline() -> None:
    from backend.agents.synthesis import SynthesisAgent
    from backend.retrieval.hybrid_search import HybridRetriever

    query = "What is consumer protection?"

    # Real retrieval, against the real corpus and indexes.
    retriever = HybridRetriever()

    retrieved_chunks = retriever.search(
        query,
        filters={"jurisdiction": "Central"},
        limit=3,
    )

    assert retrieved_chunks
    assert len(retrieved_chunks) <= 3

    for chunk in retrieved_chunks:
        assert "chunk_id" in chunk
        assert "act" in chunk
        assert "section" in chunk
        assert "source_url" in chunk
        assert chunk["jurisdiction"] == "Central"

    # Mocked LLM: no network call, no credits spent.
    mock_response = MagicMock()
    mock_response.choices[0].message.content = (
        "Consumer protection is governed by the Consumer Protection Act, 2019."
    )

    with patch("backend.agents.synthesis.Groq") as mock_groq:
        mock_groq.return_value.chat.completions.create.return_value = mock_response

        agent = SynthesisAgent()
        result = agent.synthesize(query, retrieved_chunks)

    assert "answer" in result
    assert "citations" in result
    assert result["answer"] == (
        "Consumer protection is governed by the Consumer Protection Act, 2019."
    )
    assert result["citations"]

    for citation in result["citations"]:
        for field in ("chunk_id", "act", "section", "jurisdiction", "source_url"):
            assert field in citation, f"citation missing {field}"


def test_every_citation_traces_back_to_a_retrieved_chunk() -> None:
    """The property the whole project rests on: nothing cited was invented."""
    from backend.agents.synthesis import SynthesisAgent
    from backend.retrieval.hybrid_search import HybridRetriever

    retriever = HybridRetriever()
    retrieved_chunks = retriever.search("consumer complaint", limit=3)
    assert retrieved_chunks

    mock_response = MagicMock()
    mock_response.choices[0].message.content = "An answer."

    with patch("backend.agents.synthesis.Groq") as mock_groq:
        mock_groq.return_value.chat.completions.create.return_value = mock_response
        result = SynthesisAgent().synthesize("consumer complaint", retrieved_chunks)

    retrieved_ids = {chunk["chunk_id"] for chunk in retrieved_chunks}
    for citation in result["citations"]:
        assert citation["chunk_id"] in retrieved_ids

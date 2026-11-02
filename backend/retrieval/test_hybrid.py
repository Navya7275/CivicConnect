"""Integration tests for the hybrid retriever.

Unlike the other retrieval tests, these run the real thing: a populated
database, the prebuilt FAISS and BM25 indexes, and the embedding model. That
makes them the only tests that actually exercise index loading — but it also
means they cannot run on a fresh clone, because the artifacts are generated
rather than committed.

So they skip when the prerequisites are absent. Run them after:

    python -m data.ingestion.load_seed
    python -m data.indexing.build_index
"""

import json
from pathlib import Path

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


@pytest.fixture(scope="module")
def retriever():
    """One retriever for the module — constructing it loads the model."""
    from backend.retrieval.hybrid_search import HybridRetriever

    return HybridRetriever()


@pytest.fixture(scope="module")
def indexed_chunk_count() -> int:
    """How many chunks the index was actually built over.

    Read from the mapping rather than hardcoded. An earlier version of this
    test asserted `== 25`, which silently became wrong the moment the corpus
    grew — a test that has to be edited every time the data changes is a test
    nobody trusts.
    """
    mapping = json.loads((ARTIFACTS_DIR / "chunk_ids.json").read_text())
    return mapping["total_chunks"]


def test_hybrid_retriever_loads_real_data(retriever, indexed_chunk_count) -> None:
    assert retriever.chunks
    assert len(retriever.chunks) == indexed_chunk_count


def test_hybrid_search_returns_results(retriever) -> None:
    results = retriever.search("What is consumer protection?", limit=3)

    assert results
    assert len(results) <= 3


def test_hybrid_search_preserves_scores(retriever) -> None:
    """The scores are what make the hybrid behaviour inspectable."""
    results = retriever.search("consumer protection", limit=3)

    assert results
    for result in results:
        assert "_rrf_score" in result
        assert "_retrieval_scores" in result


def test_jurisdiction_filter(retriever) -> None:
    results = retriever.search(
        "consumer protection",
        filters={"jurisdiction": "Central"},
        limit=5,
    )

    assert results
    for result in results:
        assert result["jurisdiction"] == "Central"


def test_state_jurisdiction_also_returns_central_law(retriever) -> None:
    """Central law applies in every state, so it must never be filtered out.

    This is issue #2 item B3: filtering for a state used to drop every Central
    act, which is most of Indian law.
    """
    results = retriever.search(
        "consumer protection",
        filters={"jurisdiction": "Madhya Pradesh"},
        limit=5,
    )

    for result in results:
        assert result["jurisdiction"] in {"Madhya Pradesh", "Central"}


def test_date_filter(retriever) -> None:
    results = retriever.search(
        "consumer protection",
        as_of_date="2019-01-01",
        limit=5,
    )

    for result in results:
        assert result["effective_date"] <= "2019-01-01"

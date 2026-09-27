from backend.retrieval.hybrid_search import HybridRetriever


def test_hybrid_retriever_loads_real_data():
    retriever = HybridRetriever()

    assert len(retriever.chunks) == 25


def test_hybrid_search_returns_results():
    retriever = HybridRetriever()

    results = retriever.search(
        "What is consumer protection?",
        limit=3
    )

    assert results
    assert len(results) <= 3


def test_hybrid_search_preserves_scores():
    retriever = HybridRetriever()

    results = retriever.search(
        "consumer protection",
        limit=3
    )

    assert results

    for result in results:
        assert "_rrf_score" in result
        assert "_retrieval_scores" in result


def test_jurisdiction_filter():
    retriever = HybridRetriever()

    results = retriever.search(
        "consumer protection",
        filters={"jurisdiction": "Central"},
        limit=5
    )

    assert results

    for result in results:
        assert result["jurisdiction"] == "Central"


def test_date_filter():
    retriever = HybridRetriever()

    results = retriever.search(
        "consumer protection",
        as_of_date="2019-01-01",
        limit=5
    )

    for result in results:
        assert result["effective_date"] <= "2019-01-01"
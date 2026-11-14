from backend.retrieval.chunks import get_mock_chunks
from backend.retrieval.fusion import reciprocal_rank_fusion


def test_reciprocal_rank_fusion():
    chunks = get_mock_chunks()

    bm25_results = [
        {
            **chunks[0],
            "_score": 2.5,
            "_retriever": "bm25",
        },
        {
            **chunks[1],
            "_score": 1.8,
            "_retriever": "bm25",
        },
        {
            **chunks[2],
            "_score": 1.2,
            "_retriever": "bm25",
        },
    ]

    dense_results = [
        {
            **chunks[0],
            "_score": 0.9,
            "_retriever": "dense",
        },
        {
            **chunks[2],
            "_score": 0.7,
            "_retriever": "dense",
        },
        {
            **chunks[1],
            "_score": 0.5,
            "_retriever": "dense",
        },
    ]

    results = reciprocal_rank_fusion(
        [bm25_results, dense_results],
        limit=3
    )

    assert results
    assert len(results) == 3

    for result in results:
        assert "chunk_id" in result
        assert "_rrf_score" in result
        assert "_retrieval_scores" in result

    # Every chunk appeared in both retrievers.
    # Therefore each should preserve both original scores.
    for result in results:
        scores = result["_retrieval_scores"]

        assert "bm25" in scores
        assert "dense" in scores


def test_rrf_combines_rankings():
    chunks = get_mock_chunks()

    bm25_results = [
        {
            **chunks[0],
            "_score": 2.0,
            "_retriever": "bm25",
        },
        {
            **chunks[1],
            "_score": 1.0,
            "_retriever": "bm25",
        },
    ]

    dense_results = [
        {
            **chunks[1],
            "_score": 0.9,
            "_retriever": "dense",
        },
        {
            **chunks[0],
            "_score": 0.8,
            "_retriever": "dense",
        },
    ]

    results = reciprocal_rank_fusion(
        [bm25_results, dense_results],
        limit=2
    )

    assert len(results) == 2

    # Both chunks have rank 1 once and rank 2 once,
    # so their RRF scores should be equal.
    assert results[0]["_rrf_score"] == results[1]["_rrf_score"]
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

def _result(chunk_id, retriever):
    return {"chunk_id": chunk_id, "_retriever": retriever, "_score": 1.0}


def test_default_k_lets_agreement_outrank_confidence() -> None:
    """Document the property that makes hybrid score below dense alone.

    A chunk contributes 1/(k + rank) per list. With the shipped k=60 and the
    50-candidate pool HybridRetriever uses, the best a single list can give
    is 1/61 = 0.0164, while two lists agreeing at the very bottom give
    2/110 = 0.0182. So anything both retrievers return beats anything only
    one returns, however confident that one was.

    This is not a bug to fix here -- it is the documented behaviour of RRF
    with these constants, and changing the default would change every
    existing result. The test exists so that the day someone does change it,
    the reason is in front of them.
    """
    bm25 = [_result(f"junk{i}", "bm25") for i in range(1, 25)] + [_result("AGREED", "bm25")]
    dense = ([_result("DENSE_BEST", "dense")]
             + [_result(f"d{i}", "dense") for i in range(1, 24)]
             + [_result("AGREED", "dense")])

    top = [r["chunk_id"] for r in reciprocal_rank_fusion([bm25, dense], limit=3)]
    assert top[0] == "AGREED", (
        "a chunk both retrievers rank 25th should outrank dense's first pick "
        "at k=60; if this changed, the recall figures in the report did too"
    )
    assert "DENSE_BEST" in top


def test_weighting_restores_the_stronger_retriever() -> None:
    """Weighting the dense arm puts its top pick back on top.

    Measured over 109 questions, dense beats hybrid on every body of law in
    the corpus, by as much as 28 points on the Motor Vehicles Act. The dial
    that addresses it is this one.
    """
    bm25 = [_result(f"junk{i}", "bm25") for i in range(1, 25)] + [_result("AGREED", "bm25")]
    dense = ([_result("DENSE_BEST", "dense")]
             + [_result(f"d{i}", "dense") for i in range(1, 24)]
             + [_result("AGREED", "dense")])

    weighted = reciprocal_rank_fusion([bm25, dense], limit=3, weights=[1.0, 3.0])
    assert weighted[0]["chunk_id"] == "DENSE_BEST"


def test_weights_default_to_unweighted_and_are_length_checked() -> None:
    """Omitting weights must not change a single existing score."""
    lists = [[_result("a", "bm25"), _result("b", "bm25")],
             [_result("b", "dense"), _result("a", "dense")]]

    plain = reciprocal_rank_fusion(lists, limit=2)
    ones = reciprocal_rank_fusion(lists, limit=2, weights=[1.0, 1.0])
    assert [r["chunk_id"] for r in plain] == [r["chunk_id"] for r in ones]
    assert [r["_rrf_score"] for r in plain] == [r["_rrf_score"] for r in ones]

    import pytest
    with pytest.raises(ValueError):
        reciprocal_rank_fusion(lists, weights=[1.0])


def test_hybrid_fusion_settings_are_the_measured_ones() -> None:
    """The hybrid's k and weights were chosen by measurement, not by default.

    Swept over 109 questions and 963 chunks (data/eval/tune_fusion.py):

        k=60, equal weights (the RRF paper's defaults)   68% recall@10
        k=5,  dense x3                                   77% recall@10

    Reverting to the defaults costs nine points, so the values are asserted
    rather than left to drift. If a later sweep finds better ones, change
    them here and in hybrid_search together -- the point is that they are a
    result, not a guess.
    """
    from backend.retrieval import hybrid_search

    assert hybrid_search.FUSION_K == 5
    assert hybrid_search.BM25_WEIGHT == 1.0
    assert hybrid_search.DENSE_WEIGHT == 3.0
    assert hybrid_search.DENSE_WEIGHT > hybrid_search.BM25_WEIGHT, (
        "dense reaches 77% recall against bm25's 42%; the weaker arm must "
        "not be able to overrule the stronger one"
    )

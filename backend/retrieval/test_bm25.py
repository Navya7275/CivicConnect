from unittest.mock import MagicMock

from backend.retrieval.bm25 import BM25Retriever
from backend.retrieval.chunks import get_mock_chunks


def test_bm25_search():
    chunks = get_mock_chunks()

    retriever = BM25Retriever.__new__(BM25Retriever)

    retriever.chunks = chunks
    retriever.bm25 = MagicMock()

    retriever.bm25.get_scores.return_value = [
        2.5,
        1.2,
        0.4
    ]

    results = retriever.search(
        "cheque dishonour Section 138",
        limit=3
    )

    assert results
    assert len(results) == 3

    assert results[0]["chunk_id"] == chunks[0]["chunk_id"]
    assert results[0]["_score"] == 2.5

    for chunk in results:
        assert "chunk_id" in chunk
        assert "section" in chunk
        assert "act" in chunk
        assert "_score" in chunk
        assert chunk["_retriever"] == "bm25"
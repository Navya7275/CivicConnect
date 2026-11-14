from unittest.mock import MagicMock

from backend.retrieval.bm25 import BM25Retriever
from backend.retrieval.chunks import get_mock_chunks


def _retriever_with(chunks, scores):
    """Build a BM25Retriever without touching the index files on disk.

    `__init__` reads `bm25.pkl` and `chunk_ids.json`, neither of which exists
    on a fresh clone, so the tests bypass it and inject what it would have
    loaded. The index-position -> chunk_id mapping is part of that: the
    retriever resolves results through it rather than by list position.
    """
    retriever = BM25Retriever.__new__(BM25Retriever)

    retriever.chunks = chunks
    retriever.chunk_lookup = {chunk["chunk_id"]: chunk for chunk in chunks}
    retriever.index_to_chunk_id = {
        index: chunk["chunk_id"] for index, chunk in enumerate(chunks)
    }

    retriever.bm25 = MagicMock()
    retriever.bm25.get_scores.return_value = scores

    return retriever


def test_bm25_search():
    chunks = get_mock_chunks()

    retriever = _retriever_with(chunks, [2.5, 1.2, 0.4])

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


def test_results_are_ordered_by_score():
    chunks = get_mock_chunks()

    # Lowest score first in the array, so ordering has to come from the scores
    # rather than from the array order.
    retriever = _retriever_with(chunks, [0.4, 2.5, 1.2])

    results = retriever.search("cheque dishonour", limit=3)

    assert [r["chunk_id"] for r in results] == [
        chunks[1]["chunk_id"],
        chunks[2]["chunk_id"],
        chunks[0]["chunk_id"],
    ]
    assert [r["_score"] for r in results] == [2.5, 1.2, 0.4]


def test_a_subset_of_the_corpus_does_not_raise():
    """The index knows the whole corpus; the caller may hold only part of it.

    Resolving by list position used to raise IndexError here, because the
    score array is longer than the chunk list it was being indexed into.
    """
    chunks = get_mock_chunks()
    subset = chunks[1:]                      # 2 chunks, index still has 3 scores

    retriever = BM25Retriever.__new__(BM25Retriever)
    retriever.chunks = subset
    retriever.chunk_lookup = {c["chunk_id"]: c for c in subset}
    # The mapping still covers every indexed position, as the real file does.
    retriever.index_to_chunk_id = {
        index: chunk["chunk_id"] for index, chunk in enumerate(chunks)
    }
    retriever.bm25 = MagicMock()
    retriever.bm25.get_scores.return_value = [9.9, 1.2, 0.4]   # top score is c0

    results = retriever.search("anything", limit=3)

    # c0 scored highest but is not in the subset, so it must not come back.
    returned = {r["chunk_id"] for r in results}
    assert returned == {c["chunk_id"] for c in subset}
    assert chunks[0]["chunk_id"] not in returned


def test_limit_is_respected_after_skipping_unavailable_chunks():
    chunks = get_mock_chunks()
    subset = chunks[:1]

    retriever = BM25Retriever.__new__(BM25Retriever)
    retriever.chunks = subset
    retriever.chunk_lookup = {c["chunk_id"]: c for c in subset}
    retriever.index_to_chunk_id = {
        index: chunk["chunk_id"] for index, chunk in enumerate(chunks)
    }
    retriever.bm25 = MagicMock()
    retriever.bm25.get_scores.return_value = [0.4, 2.5, 1.2]

    results = retriever.search("anything", limit=5)

    assert len(results) == 1
    assert results[0]["chunk_id"] == subset[0]["chunk_id"]

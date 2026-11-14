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


# --------------------------------------------------------------------------
# Tokenizer agreement between the index and the query
#
# BM25 matches tokens literally, so the documents and the query must be
# tokenized identically. These guard the bug where they were not: the query
# path had its own inlined copy of the tokenizer, so "request?" in a question
# never matched "request." in a statute, and the provision that answered the
# question ranked 54th instead of 2nd.
# --------------------------------------------------------------------------

import json
from pathlib import Path

import pytest

from data.indexing.build_index import TOKENIZER_VERSION, tokenize_text

ARTIFACTS = Path(__file__).resolve().parents[2] / "data" / "indexing" / "artifacts"


def test_tokenizer_strips_punctuation() -> None:
    """Punctuation must never stay glued to a word."""
    assert tokenize_text("an RTI request?") == ["an", "rti", "request"]
    assert tokenize_text("receipt of request.") == ["receipt", "of", "request"]
    assert tokenize_text("Section 7, sub-section (1)") == [
        "section", "7", "sub", "section", "1",
    ]


def test_query_and_document_tokenizers_are_the_same_function() -> None:
    """The query path must not carry its own copy of the tokenizer.

    The two drifted apart once already. This asserts the shared function is
    what actually runs on a query, so a second implementation reappearing is a
    failing test rather than a silent retrieval regression.
    """
    import inspect

    from backend.retrieval import bm25 as bm25_module

    source = inspect.getsource(bm25_module.BM25Retriever.search)
    # Strip comments, so the prose explaining the old bug does not trip this.
    code = "\n".join(
        line.split("#", 1)[0] for line in source.splitlines()
    )

    assert "tokenize_text(query)" in code, "search() must use the shared tokenizer"
    assert ".split()" not in code, "search() has its own tokenizer again"


@pytest.mark.skipif(
    not (ARTIFACTS / "bm25.pkl").exists() or not (ARTIFACTS / "chunk_ids.json").exists(),
    reason="index artifacts missing; run `python -m data.indexing.build_index` first",
)
def test_index_records_the_tokenizer_it_was_built_with() -> None:
    """A stale index must be detectable, not silently wrong."""
    mapping = json.loads((ARTIFACTS / "chunk_ids.json").read_text(encoding="utf-8"))
    assert mapping.get("tokenizer_version") == TOKENIZER_VERSION, (
        "index tokenizer_version does not match the code; "
        "run `python -m data.indexing.build_index`"
    )


@pytest.mark.skipif(
    not (ARTIFACTS / "bm25.pkl").exists() or not (ARTIFACTS / "chunk_ids.json").exists(),
    reason="index artifacts missing; run `python -m data.indexing.build_index` first",
)
def test_rti_response_time_question_retrieves_section_7() -> None:
    """Regression: the question that exposed the tokenizer bug.

    "How long does a public authority have to respond to an RTI request?" is
    answered by RTI Act Section 7, which says "within thirty days of receipt of
    request". With punctuation glued to tokens it ranked 54th, far outside any
    candidate limit, so synthesis correctly answered that it did not have the
    provision -- a right answer to the wrong retrieval.
    """
    from data.db.database import SessionLocal
    from data.db.models import Chunk

    db = SessionLocal()
    try:
        chunks = [
            {
                "chunk_id": c.chunk_id,
                "text": c.text,
                "act": c.act,
                "section": c.section,
                "jurisdiction": c.jurisdiction,
                "source_url": c.source_url,
            }
            for c in db.query(Chunk).all()
        ]
    finally:
        db.close()

    if not chunks:
        pytest.skip("database is empty; run `python -m data.ingestion.load_seed` first")

    retriever = BM25Retriever(chunks)
    results = retriever.search(
        "How long does a public authority have to respond to an RTI request?",
        limit=8,
    )

    found = [
        r.get("chunk", r) for r in results
        if (r.get("chunk", r)).get("section") == "Section 7"
        and "Right to Information" in str((r.get("chunk", r)).get("act"))
    ]
    assert found, (
        "RTI Act Section 7 is not in the top 8 for the question it answers. "
        "The query and document tokenizers have probably diverged again."
    )

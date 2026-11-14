"""Unit tests for the dense retriever.

Fully mocked: the FAISS index and the embedding model are both stand-ins, so
nothing is loaded from disk and no model is downloaded. The import is still
guarded, because `dense.py` imports sentence-transformers at module level and
that is a multi-gigabyte dependency a contributor may not have installed yet.
"""

from unittest.mock import MagicMock

import numpy as np
import pytest

pytest.importorskip(
    "sentence_transformers",
    reason="sentence-transformers is not installed; pip install -r requirements.txt",
)

from backend.retrieval.chunks import get_mock_chunks       # noqa: E402
from backend.retrieval.dense import DenseRetriever         # noqa: E402


def test_dense_search():
    chunks = get_mock_chunks()

    retriever = DenseRetriever.__new__(DenseRetriever)

    retriever.chunks = chunks
    retriever.chunk_lookup = {
        chunk["chunk_id"]: chunk
        for chunk in chunks
    }

    retriever.index = MagicMock()

    retriever.model = MagicMock()

    retriever.model.encode.return_value = np.array(
        [[0.1, 0.2, 0.3]],
        dtype="float32"
    )

    retriever.index.search.return_value = (
        np.array([[0.95, 0.80, 0.60]], dtype="float32"),
        np.array([[0, 1, 2]], dtype="int64")
    )

    retriever.index_to_chunk_id = {
        0: chunks[0]["chunk_id"],
        1: chunks[1]["chunk_id"],
        2: chunks[2]["chunk_id"],
    }

    results = retriever.search(
        "What happens when a cheque bounces because there is not enough money?",
        limit=3
    )

    assert results
    assert len(results) == 3

    assert results[0]["chunk_id"] == chunks[0]["chunk_id"]
    assert results[0]["_score"] == pytest.approx(0.95)

    for chunk in results:
        assert "chunk_id" in chunk
        assert "section" in chunk
        assert "act" in chunk
        assert "_score" in chunk
        assert chunk["_retriever"] == "dense"
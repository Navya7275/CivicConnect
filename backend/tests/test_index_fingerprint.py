import json
import pytest
from backend.retrieval.bm25 import BM25Retriever, CHUNK_IDS_PATH


def test_index_fingerprint_mismatch_raises():
    """Assert that when the corpus fingerprint in chunk_ids.json does not match disk, loading raises."""
    with open(CHUNK_IDS_PATH, "r", encoding="utf-8") as f:
        original_mapping = json.load(f)

    try:
        # Tamper with the fingerprint
        tampered = dict(original_mapping)
        tampered["corpus_sha256"] = "invalid_hash_00000000000000000000000000000000"
        with open(CHUNK_IDS_PATH, "w", encoding="utf-8") as f:
            json.dump(tampered, f)

        # Loading retriever must raise RuntimeError
        with pytest.raises(RuntimeError, match="Index was built from a different corpus"):
            BM25Retriever(chunks=[])
    finally:
        # Restore original mapping
        with open(CHUNK_IDS_PATH, "w", encoding="utf-8") as f:
            json.dump(original_mapping, f, indent=2)

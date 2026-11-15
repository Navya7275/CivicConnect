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


def test_fingerprint_is_the_same_on_windows_and_linux(tmp_path):
    """The corpus fingerprint must not depend on how git checked the files out.

    This is a regression test for a real failure. The first implementation
    hashed the raw bytes of seed_chunks.json and seed_schemes.json. git
    normalises line endings on checkout, so a Windows clone with core.autocrlf
    holds CRLF where a Linux clone holds LF, and the identical corpus hashed to
    two different values.

    The result was a guard that fired everywhere except the machine that built
    the index: the committed fingerprint matched only the CRLF form, so every
    other clone and CI refused to load an index that was perfectly valid.

    Hashing canonical JSON instead -- parsed, keys sorted, no incidental
    whitespace -- fixes it, and also means reformatting a corpus file does not
    invalidate the index. Only a change in content does, which is what the
    fingerprint is for.
    """
    import json as _json

    from data.indexing.build_index import corpus_fingerprint

    corpus = [{"chunk_id": "a-1", "text": "first"}, {"chunk_id": "a-2", "text": "second"}]

    lf_file = tmp_path / "lf.json"
    lf_file.write_bytes(_json.dumps(corpus, indent=2).encode("utf-8"))

    crlf_dir = tmp_path / "crlf"
    crlf_dir.mkdir()
    crlf_file = crlf_dir / "lf.json"
    crlf_file.write_bytes(lf_file.read_bytes().replace(b"\n", b"\r\n"))

    assert b"\r\n" in crlf_file.read_bytes(), "the CRLF fixture must actually contain CRLF"

    assert corpus_fingerprint([lf_file]) == corpus_fingerprint([crlf_file]), (
        "the fingerprint changed with line endings, so an index built on one "
        "platform will refuse to load on another"
    )


def test_fingerprint_still_changes_when_content_changes(tmp_path):
    """Being insensitive to formatting must not make it insensitive to content."""
    import json as _json

    from data.indexing.build_index import corpus_fingerprint

    a = tmp_path / "corpus.json"
    a.write_text(_json.dumps([{"chunk_id": "a-1", "text": "first"}]), encoding="utf-8")
    before = corpus_fingerprint([a])

    a.write_text(_json.dumps([{"chunk_id": "a-1", "text": "first amended"}]), encoding="utf-8")
    assert corpus_fingerprint([a]) != before

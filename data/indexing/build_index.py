"""Script to build Dense FAISS Vector Index and Sparse BM25 Index from PostgreSQL database chunks.

Features:
- Reads active chunks directly from PostgreSQL
- Embeds chunk texts using sentence-transformers model (configurable via EMBEDDING_MODEL env var)
- Builds FAISS dense vector index
- Builds BM25 sparse index using rank_bm25
- Preserves explicit bidirectional index position -> chunk_id mappings
- Saves index artifacts reproducibly in data/indexing/artifacts/
"""

import hashlib
import json
import os
import pickle
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from data.db.database import SessionLocal
from data.db.models import Chunk

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

SEED_CHUNKS_PATH = Path(__file__).resolve().parents[1] / "ingestion" / "seed_chunks.json"
SEED_SCHEMES_PATH = Path(__file__).resolve().parents[1] / "ingestion" / "seed_schemes.json"


# Incremented whenever tokenize_text changes behaviour. Written into
# chunk_ids.json at build time and checked when the BM25 index is loaded, so a
# tokenizer change cannot silently mismatch an index built by the old one.
#   1 = text.split(), punctuation left attached to words
#   2 = alphanumeric runs, punctuation stripped
TOKENIZER_VERSION = 2

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def corpus_fingerprint(paths) -> str:
    """Hash the corpus by content, in a way that is the same on every machine.

    Hashing the raw bytes of these files does not work in a git repository.
    git normalises line endings on checkout, so a Windows clone with
    core.autocrlf sees CRLF where a Linux clone sees LF, and the same corpus
    hashes to two different values. An index built on Windows then refuses to
    load everywhere else -- which is what happened: the committed fingerprint
    matched only the CRLF form, so the guard fired for every other machine and
    for CI, while passing on the laptop that wrote it.

    So the hash is taken over canonical JSON instead: parsed, keys sorted, no
    incidental whitespace. That is immune to line endings and to reformatting,
    and it tracks what the fingerprint is actually meant to track -- whether
    the corpus CONTENT changed, not whether the file was re-indented.
    """
    import hashlib
    import json as _json

    digest = hashlib.sha256()
    for path in sorted(str(p) for p in paths):
        p = Path(path)
        if not p.exists():
            continue
        data = _json.loads(p.read_text(encoding="utf-8"))
        canonical = _json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        digest.update(p.name.encode("utf-8"))
        digest.update(canonical.encode("utf-8"))
    return digest.hexdigest()


def tokenize_text(text: str) -> List[str]:
    """Tokenize text for BM25 indexing (lowercased alphanumeric tokens).

    Splits on anything that is not a letter or digit, so punctuation never ends
    up glued to a word. This function is used for both the documents and the
    query, so the two sides have to agree -- a token only matches if it is
    produced identically on both.

    It previously did `text.split()`, which splits on whitespace alone and
    keeps punctuation attached. That silently broke keyword matching for any
    word next to punctuation, which in practice is every sentence-final word in
    a statute and every word before a question mark in a query:

        document "...receipt of request."  ->  "request."
        query    "...an RTI request?"      ->  "request?"

    Neither matches the other, nor the bare "request". For the question "How
    long does a public authority have to respond to an RTI request?", the RTI
    Act Section 7 chunk -- which is exactly the provision that answers it, and
    contains "request" twice -- ranked 54th. With punctuation stripped it ranks
    1st.

    Note that stopwords are deliberately NOT removed. BM25 already down-weights
    common terms through IDF, and in statutory text the small words carry real
    meaning: "not", "shall", "may" and "within" change what a provision does.
    """
    return _TOKEN_RE.findall(text.lower())


def build_indexes(model_name: str = DEFAULT_MODEL_NAME) -> Dict[str, str]:
    """Build Dense Vector Index and Sparse BM25 Index from DB chunks."""
    print(f"Connecting to database to fetch searchable chunks...")
    db = SessionLocal()

    try:
        chunks: List[Chunk] = db.query(Chunk).order_by(Chunk.id).all()
        if not chunks:
            raise ValueError("No chunks found in database. Load seed/ingestion data first.")

        chunk_ids = [c.chunk_id for c in chunks]
        texts = [c.text for c in chunks]

        print(f"Fetched {len(chunks)} chunks from database.")

        # 1. Build Dense Vector Index (FAISS)
        print(f"Loading embedding model: '{model_name}'...")
        embedder = SentenceTransformer(model_name)

        print("Generating dense vector embeddings...")
        embeddings = embedder.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        embeddings = np.array(embeddings).astype("float32")

        # Normalize vectors for cosine similarity
        faiss.normalize_L2(embeddings)

        vector_dim = embeddings.shape[1]
        faiss_index = faiss.IndexFlatIP(vector_dim)  # Inner Product on normalized vectors = Cosine Similarity
        faiss_index.add(embeddings)

        faiss_file = ARTIFACTS_DIR / "faiss.index"
        faiss.write_index(faiss_index, str(faiss_file))
        print(f"Dense FAISS index saved to: {faiss_file}")

        # 2. Build Sparse BM25 Index
        print("Tokenizing texts for BM25 index...")
        tokenized_corpus = [tokenize_text(t) for t in texts]
        bm25_index = BM25Okapi(tokenized_corpus)

        bm25_file = ARTIFACTS_DIR / "bm25.pkl"
        with open(bm25_file, "wb") as f:
            pickle.dump(bm25_index, f)
        print(f"Sparse BM25 index saved to: {bm25_file}")

        # 3. Save chunk_id mappings & fingerprint
        mapping_file = ARTIFACTS_DIR / "chunk_ids.json"

        fingerprint = corpus_fingerprint([SEED_CHUNKS_PATH, SEED_SCHEMES_PATH])

        id_mapping = {
            "index_to_chunk_id": {idx: cid for idx, cid in enumerate(chunk_ids)},
            "chunk_id_to_index": {cid: idx for idx, cid in enumerate(chunk_ids)},
            "total_chunks": len(chunk_ids),
            "embedding_model": model_name,
            "corpus_sha256": fingerprint,
            "built_at": datetime.now(timezone.utc).isoformat(),
            # Bump TOKENIZER_VERSION whenever tokenize_text changes. The BM25
            # index stores documents already tokenized, so an index built by an
            # older tokenizer cannot be queried by a newer one: the two sides
            # produce different tokens for the same word and matching silently
            # degrades. The loader refuses to use an index whose version does
            # not match, which turns that into a clear error.
            "tokenizer_version": TOKENIZER_VERSION,
        }

        with open(mapping_file, "w", encoding="utf-8") as f:
            json.dump(id_mapping, f, indent=2)
        print(f"Chunk ID mappings saved to: {mapping_file}")

        print("\nIndex Build Summary")
        print("-------------------")
        print(f"Total Chunks Indexed : {len(chunks)}")
        print(f"Dense Vector Dim     : {vector_dim}")
        print(f"FAISS Artifact       : {faiss_file.name}")
        print(f"BM25 Artifact        : {bm25_file.name}")
        print(f"Mapping Artifact     : {mapping_file.name}\n")

        return {
            "faiss": str(faiss_file),
            "bm25": str(bm25_file),
            "mapping": str(mapping_file),
        }

    finally:
        db.close()


if __name__ == "__main__":
    build_indexes()

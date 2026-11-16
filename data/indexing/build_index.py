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

from sqlalchemy.exc import OperationalError

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

    Stopwords are not removed from DOCUMENTS, because in statutory text the
    small words carry real meaning: "not", "shall", "may" and "within" change
    what a provision does. Queries are a different matter -- see
    QUERY_STOPWORDS below and filter_query_tokens().
    """
    return _TOKEN_RE.findall(text.lower())


# Words stripped from a QUERY before scoring, never from a document.
#
# The reasoning above ("IDF already handles common terms") held while the
# corpus was 75 chunks. It stopped holding at 963. rank_bm25's IDF is
# log(1 + (N - df + 0.5)/(df + 0.5)), which stays positive however common a
# term is, so a long document containing many instances of "a", "to", "an"
# and "of" keeps accumulating score. With a small corpus there was nothing to
# accumulate against; with a thousand, the function words outweigh the content
# words entirely.
#
# Measured on "How long does a public authority have to respond to an RTI
# request?": the provision that answers it, RTI Act s.7, ranked 2nd at 75
# chunks and 35th at 963. Two of the three words that should carry the query
# contribute nothing at all -- "respond" and "rti" both have df=0, because the
# Act says "reply" and spells its own name out -- so the query rests on
# "request" against 963 documents competing on "a", "to", "public" and
# "authority".
#
# Over the 69 answerable evaluation questions, filtering these lifts bm25
# recall@10 from 30% to 55%: 17 questions fixed, none broken.
#
# This list is deliberately function words only. Nothing here changes the
# meaning of a provision. Legally loaded small words are NOT included, and
# must not be added: not, no, shall, may, must, within, before, after, unless,
# until, if, than, less, more, each, any, all, other, such.
QUERY_STOPWORDS = frozenset("""
    a an the this that these those there here
    i me my we our you your it its he she they them their
    is am are was were be been being
    do does did done have has had having
    what which who whom whose when where why how
    of to in on at by for with as from into about
    and or but so then
""".split())


def filter_query_tokens(tokens: List[str]) -> List[str]:
    """Drop function words from a query, keeping at least one token.

    A query made entirely of function words ("what is it about?") would
    otherwise score nothing at all, so in that case the original tokens are
    kept and the caller gets the old behaviour rather than an empty result.
    """
    kept = [t for t in tokens if t not in QUERY_STOPWORDS]
    return kept or tokens


def build_indexes(model_name: str = DEFAULT_MODEL_NAME) -> Dict[str, str]:
    """Build Dense Vector Index and Sparse BM25 Index from DB chunks."""
    print(f"Connecting to database to fetch searchable chunks...")
    db = SessionLocal()

    SETUP_HINT = (
        "The corpus has not been loaded into the database yet. Run:\n"
        "    python -m data.ingestion.load_seed\n"
        "    python -m data.ingestion.load_welfare\n"
        "    python -m data.ingestion.validate\n"
        "and then build the index again.\n\n"
        "civicconnect.db is no longer tracked in git (it is a generated file, and\n"
        "committing it meant every run showed up as a change), so a fresh clone or\n"
        "a pull that removed it has no database until those commands create one."
    )

    try:
        try:
            chunks: List[Chunk] = db.query(Chunk).order_by(Chunk.id).all()
        except OperationalError as exc:
            # The table does not exist, which is a missing database rather than a
            # broken one. Without this the user gets forty lines of SQLAlchemy
            # traceback ending in "no such table: chunks", which says what failed
            # but not what to do.
            raise SystemExit(f"\n{SETUP_HINT}\n") from exc

        if not chunks:
            raise SystemExit(f"\nThe chunks table exists but is empty.\n\n{SETUP_HINT}\n")

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

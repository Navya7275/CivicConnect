"""Script to build Dense FAISS Vector Index and Sparse BM25 Index from PostgreSQL database chunks.

Features:
- Reads active chunks directly from PostgreSQL
- Embeds chunk texts using sentence-transformers model (configurable via EMBEDDING_MODEL env var)
- Builds FAISS dense vector index
- Builds BM25 sparse index using rank_bm25
- Preserves explicit bidirectional index position -> chunk_id mappings
- Saves index artifacts reproducibly in data/indexing/artifacts/
"""

import json
import os
import pickle
import sys
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


def tokenize_text(text: str) -> List[str]:
    """Tokenize text for BM25 indexing (lowercased alphanumeric tokens)."""
    return [token.lower() for token in text.split() if token.strip()]


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

        # 3. Save chunk_id mappings
        mapping_file = ARTIFACTS_DIR / "chunk_ids.json"
        id_mapping = {
            "index_to_chunk_id": {idx: cid for idx, cid in enumerate(chunk_ids)},
            "chunk_id_to_index": {cid: idx for idx, cid in enumerate(chunk_ids)},
            "total_chunks": len(chunk_ids),
            "embedding_model": model_name,
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

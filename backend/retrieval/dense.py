from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


ARTIFACTS_DIR = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "indexing"
    / "artifacts"
)

FAISS_INDEX_PATH = ARTIFACTS_DIR / "faiss.index"
CHUNK_IDS_PATH = ARTIFACTS_DIR / "chunk_ids.json"


class DenseRetriever:
    """
    Dense semantic retriever using the prebuilt FAISS index.
    """

    def __init__(
        self,
        chunks,
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    ):
        self.chunks = chunks

        if not FAISS_INDEX_PATH.exists():
            raise FileNotFoundError(
                f"FAISS index not found: {FAISS_INDEX_PATH}"
            )

        if not CHUNK_IDS_PATH.exists():
            raise FileNotFoundError(
                f"Chunk ID mapping not found: {CHUNK_IDS_PATH}"
            )

        # Map chunk_id -> chunk dictionary.
        self.chunk_lookup = {
            chunk["chunk_id"]: chunk
            for chunk in chunks
        }

        # Load the prebuilt FAISS index.
        self.index = faiss.read_index(
            str(FAISS_INDEX_PATH)
        )

       # Load the embedding model for this retriever instance.
        self.model = SentenceTransformer(model_name)
        # The FAISS index positions correspond to the
        # database chunk ordering used during index building.
        import json

        with open(CHUNK_IDS_PATH, "r", encoding="utf-8") as file:
            mapping = json.load(file)

        self.index_to_chunk_id = {
            int(index): chunk_id
            for index, chunk_id
            in mapping["index_to_chunk_id"].items()
        }

    def search(self, query, limit=5):
        """
        Search the prebuilt FAISS index.

        Returns:
            list[dict]: Each result contains the chunk and
            its dense similarity score.
        """

        query_embedding = self.model.encode(
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True
        ).astype("float32")

        scores, indices = self.index.search(
            query_embedding,
            limit
        )

        results = []

        for score, index in zip(
            scores[0],
            indices[0]
        ):
            if index < 0:
                continue

            chunk_id = self.index_to_chunk_id.get(
                int(index)
            )

            if chunk_id is None:
                continue

            chunk = self.chunk_lookup.get(chunk_id)

            if chunk is None:
                continue

            result = dict(chunk)
            result["_score"] = float(score)
            result["_retriever"] = "dense"

            results.append(result)

        return results
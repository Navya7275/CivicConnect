from sentence_transformers import SentenceTransformer
import numpy as np


class DenseRetriever:
    """
    Dense semantic retriever for CivicConnect.
    """

    def __init__(
        self,
        chunks,
        model_name="all-MiniLM-L6-v2"
    ):
        self.chunks = chunks

        # Load the embedding model.
        self.model = SentenceTransformer(model_name)

        # Create embeddings for all chunks.
        self.embeddings = self.model.encode(
            [chunk["text"] for chunk in chunks],
            normalize_embeddings=True
        )

    def search(self, query, limit=5):
        """
        Search chunks using semantic similarity.
        """

        # Convert query into an embedding.
        query_embedding = self.model.encode(
            query,
            normalize_embeddings=True
        )

        # Since embeddings are normalized,
        # dot product gives cosine similarity.
        scores = np.dot(
            self.embeddings,
            query_embedding
        )

        # Pair chunks with scores.
        ranked = list(zip(self.chunks, scores))

        # Highest similarity first.
        ranked.sort(
            key=lambda item: item[1],
            reverse=True
        )

        return [
            chunk
            for chunk, score in ranked[:limit]
        ]
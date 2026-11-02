from pathlib import Path
import pickle


ARTIFACTS_DIR = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "indexing"
    / "artifacts"
)

BM25_INDEX_PATH = ARTIFACTS_DIR / "bm25.pkl"


class BM25Retriever:
    """
    BM25-based sparse retriever using the prebuilt BM25 index.
    """

    def __init__(self, chunks):
        self.chunks = chunks

        if not BM25_INDEX_PATH.exists():
            raise FileNotFoundError(
                f"BM25 index not found: {BM25_INDEX_PATH}"
            )

        # Map chunk_id -> chunk dictionary.
        self.chunk_lookup = {
            chunk["chunk_id"]: chunk
            for chunk in chunks
        }

        # Load the prebuilt BM25 index.
        with open(BM25_INDEX_PATH, "rb") as file:
            self.bm25 = pickle.load(file)

    def search(self, query, limit=5):
        """
        Search the prebuilt BM25 index.

        Returns:
            list[dict]: Each result contains the chunk and
            its BM25 score.
        """

        query_tokens = [
            token.lower()
            for token in query.split()
            if token.strip()
        ]

        scores = self.bm25.get_scores(query_tokens)

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda index: scores[index],
            reverse=True
        )[:limit]

        results = []

        for index in ranked_indices:
            chunk = self.chunks[index]

            result = dict(chunk)
            result["_score"] = float(scores[index])
            result["_retriever"] = "bm25"

            results.append(result)

        return results
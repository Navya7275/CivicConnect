from pathlib import Path
import json
import pickle


ARTIFACTS_DIR = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "indexing"
    / "artifacts"
)

BM25_INDEX_PATH = ARTIFACTS_DIR / "bm25.pkl"
CHUNK_IDS_PATH = ARTIFACTS_DIR / "chunk_ids.json"


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

        if not CHUNK_IDS_PATH.exists():
            raise FileNotFoundError(
                f"Chunk ID mapping not found: {CHUNK_IDS_PATH}"
            )

        # Map chunk_id -> chunk dictionary.
        self.chunk_lookup = {
            chunk["chunk_id"]: chunk
            for chunk in chunks
        }

        # Load the prebuilt BM25 index.
        with open(BM25_INDEX_PATH, "rb") as file:
            self.bm25 = pickle.load(file)

        # Positions in the BM25 score array refer to the order the index was
        # built in, which is not necessarily the order (or the length) of the
        # `chunks` list we were handed. So resolve through the same mapping
        # dense.py uses: index position -> chunk_id -> chunk.
        #
        # Indexing `self.chunks` by score position directly looks equivalent
        # and is not: it raises IndexError when given a subset of the corpus,
        # and silently returns the wrong chunk when the index is stale.
        with open(CHUNK_IDS_PATH, "r", encoding="utf-8") as file:
            mapping = json.load(file)

        self.index_to_chunk_id = {
            int(index): chunk_id
            for index, chunk_id
            in mapping["index_to_chunk_id"].items()
        }

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
        )

        results = []

        for index in ranked_indices:
            if len(results) >= limit:
                break

            chunk_id = self.index_to_chunk_id.get(int(index))

            if chunk_id is None:
                continue

            chunk = self.chunk_lookup.get(chunk_id)

            # The caller may have passed a subset of the corpus, so a chunk
            # the index knows about is not always one we can return.
            if chunk is None:
                continue

            result = dict(chunk)
            result["_score"] = float(scores[index])
            result["_retriever"] = "bm25"

            results.append(result)

        return results

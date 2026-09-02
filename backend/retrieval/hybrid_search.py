from bm25 import BM25Retriever
from dense import DenseRetriever
from filters import filter_by_metadata
from fusion import reciprocal_rank_fusion


class HybridRetriever:
    """
    Combines BM25 retrieval, dense retrieval,
    metadata filtering, and RRF fusion.
    """

    def __init__(self, chunks):
        self.chunks = chunks

        # Initialize both retrieval systems.
        self.bm25 = BM25Retriever(chunks)
        self.dense = DenseRetriever(chunks)

    def search(
        self,
        query,
        filters=None,
        limit=5
    ):
        """
        Perform hybrid retrieval.

        Steps:
        1. Retrieve using BM25.
        2. Retrieve using dense embeddings.
        3. Apply metadata filtering.
        4. Fuse rankings using RRF.
        """

        # BM25 retrieval
        bm25_results = self.bm25.search(
            query,
            limit=limit
        )

        # Dense retrieval
        dense_results = self.dense.search(
            query,
            limit=limit
        )

        # Apply metadata filters.
        bm25_results = filter_by_metadata(
            bm25_results,
            filters
        )

        dense_results = filter_by_metadata(
            dense_results,
            filters
        )

        # Combine rankings.
        results = reciprocal_rank_fusion(
            [bm25_results, dense_results],
            limit=limit
        )

        return results
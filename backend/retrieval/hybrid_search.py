from .bm25 import BM25Retriever
from .data_loader import load_chunks_from_database
from .dense import DenseRetriever
from .filters import filter_by_metadata
from .fusion import reciprocal_rank_fusion


class HybridRetriever:
    """
    Hybrid retriever using real database chunks,
    prebuilt FAISS and BM25 indexes, metadata filtering,
    date filtering, and RRF fusion.
    """

    def __init__(self, chunks=None):
        # Use real database chunks by default.
        if chunks is None:
            chunks = load_chunks_from_database()

        self.chunks = chunks

        # Load the prebuilt retrieval indexes.
        self.bm25 = BM25Retriever(chunks)
        self.dense = DenseRetriever(chunks)

    def search(
        self,
        query,
        filters=None,
        as_of_date=None,
        limit=5
    ):
        """
        Perform hybrid retrieval.

        Steps:
        1. Load/filter eligible chunks.
        2. Search the prebuilt BM25 index.
        3. Search the prebuilt FAISS index.
        4. Keep only eligible chunks.
        5. Fuse results using RRF.
        """

        # Apply metadata and effective-date filters first.
        filtered_chunks = filter_by_metadata(
            self.chunks,
            filters=filters,
            as_of_date=as_of_date
        )

        if not filtered_chunks:
            return []

        eligible_ids = {
            chunk["chunk_id"]
            for chunk in filtered_chunks
        }

        # Retrieve extra candidates so filtering does not
        # accidentally leave us with too few results.
        candidate_limit = min(
            len(self.chunks),
            max(limit * 5, limit)
        )

        # Search prebuilt BM25 index.
        bm25_results = self.bm25.search(
            query,
            limit=candidate_limit
        )

        # Search prebuilt FAISS index.
        dense_results = self.dense.search(
            query,
            limit=candidate_limit
        )

        # Keep only chunks that passed metadata/date filters.
        bm25_results = [
            chunk
            for chunk in bm25_results
            if chunk["chunk_id"] in eligible_ids
        ]

        dense_results = [
            chunk
            for chunk in dense_results
            if chunk["chunk_id"] in eligible_ids
        ]

        # Fuse the two ranked lists.
        results = reciprocal_rank_fusion(
            [bm25_results, dense_results],
            limit=limit
        )

        return results
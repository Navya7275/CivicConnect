from .bm25 import BM25Retriever
from .data_loader import load_chunks_from_database
from .dense import DenseRetriever
from .filters import filter_by_metadata
from .fusion import reciprocal_rank_fusion

# Fusion settings, chosen by measurement rather than by the RRF paper's
# defaults. data/eval/tune_fusion.py sweeps them; these were the best of
# 25 combinations over 109 questions and 963 chunks.
#
#   k=60, equal weights (the paper's defaults)  68% recall@10
#   k=5,  dense x3                              77% recall@10
#
# k=60 was tuned in the original paper across TREC runs of comparable
# quality. These two arms are not comparable: dense reaches 77% and bm25
# 42%. At k=60 with a 50-candidate pool, anything both arms return beats
# anything only one returns -- 2/110 > 1/61 -- so agreement outvoted dense's
# top pick and the fusion cost up to 28 points on a body of law.
#
# Lowering k makes rank matter again (dense's first pick survives agreement
# at rank r once k < r-2) and the weight states which arm is trusted.
#
# What this does NOT do is make the hybrid better than dense. At these
# settings it returns exactly dense's result set -- same 84 questions, none
# gained, none lost. bm25 uniquely finds 3 of 109, which is +2.8 points
# against a +/-4.0 point standard error, so the honest reading is that the
# second arm contributes nothing measurable on this corpus. It is kept
# because it costs little and a larger or differently-worded question set
# may yet separate them; it is weighted down because on the evidence it
# should not be allowed to overrule the arm that works.
FUSION_K = 5
BM25_WEIGHT = 1.0
DENSE_WEIGHT = 3.0


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
            k=FUSION_K,
            limit=limit,
            weights=[BM25_WEIGHT, DENSE_WEIGHT]
        )

        return results
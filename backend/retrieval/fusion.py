def reciprocal_rank_fusion(
    result_lists,
    k=60,
    limit=5
):
    """
    Combine ranked retrieval results using Reciprocal Rank Fusion.

    Each result may contain:
        - chunk_id
        - _score
        - _retriever

    The returned chunk contains:
        - _rrf_score
        - _retrieval_scores
    """

    scores = {}
    chunk_lookup = {}
    retrieval_scores = {}

    for results in result_lists:

        for rank, chunk in enumerate(results, start=1):

            chunk_id = chunk["chunk_id"]

            chunk_lookup[chunk_id] = chunk

            rrf_score = 1 / (k + rank)

            scores[chunk_id] = (
                scores.get(chunk_id, 0)
                + rrf_score
            )

            retriever_name = chunk.get(
                "_retriever",
                "unknown"
            )

            retrieval_scores.setdefault(
                chunk_id,
                {}
            )

            retrieval_scores[chunk_id][
                retriever_name
            ] = chunk.get("_score")

    ranked_ids = sorted(
        scores,
        key=scores.get,
        reverse=True
    )

    results = []

    for chunk_id in ranked_ids[:limit]:

        result = dict(
            chunk_lookup[chunk_id]
        )

        result["_rrf_score"] = scores[chunk_id]

        result["_retrieval_scores"] = (
            retrieval_scores[chunk_id]
        )

        results.append(result)

    return results
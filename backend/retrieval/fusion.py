def reciprocal_rank_fusion(
    result_lists,
    k=60,
    limit=5
):
    """
    Combine multiple ranked result lists using
    Reciprocal Rank Fusion (RRF).
    """

    scores = {}
    chunk_lookup = {}

    for results in result_lists:

        for rank, chunk in enumerate(results, start=1):

            chunk_id = chunk["chunk_id"]

            chunk_lookup[chunk_id] = chunk

            score = 1 / (k + rank)

            scores[chunk_id] = (
                scores.get(chunk_id, 0) + score
            )

    ranked_ids = sorted(
        scores,
        key=scores.get,
        reverse=True
    )

    return [
        chunk_lookup[chunk_id]
        for chunk_id in ranked_ids[:limit]
    ]
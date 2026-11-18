def reciprocal_rank_fusion(
    result_lists,
    k=60,
    limit=5,
    weights=None
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

    ON k AND weights
    ----------------
    A chunk's contribution from one list is weight / (k + rank), so k decides
    how much being ranked first is worth against merely appearing in both
    lists. k=60 is the figure from the original RRF paper, where it was tuned
    across TREC runs of comparable quality. That assumption does not hold
    here, and with a 50-candidate pool the arithmetic is stark:

        dense ranks it #1, bm25 never finds it : 1/61  = 0.016393
        both retrievers rank it last (#50)     : 2/110 = 0.018182

    So every chunk the two agree on outranks every chunk only one found,
    however confident that one was. Fusion stops being a ranking and becomes
    "intersection first". That is fine when both retrievers are good, and
    costly when one is not: measured over 109 questions, bm25 reaches 14% on
    criminal law against dense's 64%, and hybrid lands at 59% -- below the
    better arm on every body of law tested.

    Two dials fix it. Lower k makes rank matter more than agreement (dense's
    #1 survives agreement at rank r when k < r - 2). `weights` scales each
    list's contribution, which says plainly that one retriever is more
    trustworthy than the other.

    Defaults are unchanged, so existing behaviour is identical until a caller
    opts in. data/eval/tune_fusion.py sweeps both against the question set.
    """

    if weights is None:
        weights = [1.0] * len(result_lists)
    if len(weights) != len(result_lists):
        raise ValueError(
            f"weights has {len(weights)} entries for "
            f"{len(result_lists)} result lists"
        )

    scores = {}
    chunk_lookup = {}
    retrieval_scores = {}

    for weight, results in zip(weights, result_lists):

        for rank, chunk in enumerate(results, start=1):

            chunk_id = chunk["chunk_id"]

            chunk_lookup[chunk_id] = chunk

            rrf_score = weight / (k + rank)

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
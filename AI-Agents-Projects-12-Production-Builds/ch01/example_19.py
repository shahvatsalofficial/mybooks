def reciprocal_rank_fusion(
    bm25_order: list[str],
    dense_order: list[str],
    k: int = 60,
) -> list[tuple[str, float]]:
    scores: dict[str, float] = {}
    for rank, doc_id in enumerate(bm25_order, start=1):
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    for rank, doc_id in enumerate(dense_order, start=1):
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

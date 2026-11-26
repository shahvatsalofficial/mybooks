def dynamic_weighted_rrf(dense_ranks: List[str], sparse_ranks: List[str], query: str) -> List[Tuple[str, float]]:
    # If query contains digits or codes, heavily weight BM25 keyword search
    has_codes = bool(re.search(r"\d+|[A-Z]{3,}", query))
    dense_weight = 0.3 if has_codes else 0.7
    sparse_weight = 0.7 if has_codes else 0.3
    
    scores = {}
    for rank, doc in enumerate(dense_ranks):
        scores[doc] = scores.get(doc, 0.0) + (dense_weight / (60 + rank + 1))
    for rank, doc in enumerate(sparse_ranks):
        scores[doc] = scores.get(doc, 0.0) + (sparse_weight / (60 + rank + 1))
        
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

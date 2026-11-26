class HybridReranker:
    def __init__(self, rrf_k: int = 60):
        self.rrf_k = rrf_k

    def fuse_and_rerank(self, dense_ranks: List[str], sparse_ranks: List[str]) -> List[Tuple[str, float]]:
        scores: Dict[str, float] = {}
        
        # Dense vector RRF contribution
        for rank, doc_id in enumerate(dense_ranks):
            scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (self.rrf_k + rank + 1))
            
        # Sparse BM25 RRF contribution
        for rank, doc_id in enumerate(sparse_ranks):
            scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (self.rrf_k + rank + 1))
            
        # Sort descending by fused score
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_docs

# Verification
reranker = HybridReranker(rrf_k=60)
dense_results = ["doc_A", "doc_B", "doc_C"]
sparse_results = ["doc_C", "doc_A", "doc_D"]

fused = reranker.fuse_and_rerank(dense_results, sparse_results)
print("Hybrid Reciprocal Rank Fusion Results:")
for doc, score in fused:
    print(f"  {doc}: {score:.5f}")

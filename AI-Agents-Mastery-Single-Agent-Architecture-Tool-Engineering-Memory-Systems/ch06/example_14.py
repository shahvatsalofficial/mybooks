from typing import List, Dict

class ReciprocalRankFusionEngine:
    def __init__(self, k: int = 60):
        self.k = k

    def fuse_rankings(self, dense_ranks: List[str], sparse_ranks: List[str]) -> List[tuple[str, float]]:
        scores: Dict[str, float] = {}

        for rank, doc_id in enumerate(dense_ranks, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (self.k + rank))

        for rank, doc_id in enumerate(sparse_ranks, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (self.k + rank))

        fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return fused

rrf = ReciprocalRankFusionEngine(k=60)
dense = ["doc_A", "doc_B", "doc_C"]
sparse = ["doc_B", "doc_D", "doc_A"]
fused_results = rrf.fuse_rankings(dense, sparse)
print("Top Fused Document:", fused_results[0])

class MemoryRRFEngine:
    def __init__(self, k_constant: int = 60):
        self.k = k_constant

    def fuse_ranks(self, dense_results: List[Tuple[str, float]], sparse_results: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
        scores: Dict[str, float] = {}

        for rank, (doc_id, _) in enumerate(dense_results):
            scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (self.k + rank + 1))

        for rank, (doc_id, _) in enumerate(sparse_results):
            scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (self.k + rank + 1))

        return sorted(scores.items(), key=lambda x: x[1], reverse=True)

# Verification
rrf = MemoryRRFEngine(k_constant=60)
dense_list = [("mem_101", 0.92), ("mem_102", 0.88), ("mem_103", 0.81)]
sparse_list = [("mem_103", 4.5), ("mem_101", 2.1), ("mem_104", 1.8)]
fused_ranks = rrf.fuse_ranks(dense_list, sparse_list)
print("RRF Fused Memory Rankings:")
for m_id, sc in fused_ranks:
    print(f"  {m_id}: Score {sc:.5f}")

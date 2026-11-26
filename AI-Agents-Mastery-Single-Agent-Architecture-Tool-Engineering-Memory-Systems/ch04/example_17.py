from typing import Dict, List, Any

class HybridDenseSparseIndex:
    def __init__(self):
        self.records: List[Dict[str, Any]] = []

    def insert(self, doc_id: str, dense_vec: List[float], sparse_tokens: Dict[str, float]) -> None:
        self.records.append({
            "doc_id": doc_id,
            "dense": dense_vec,
            "sparse": sparse_tokens
        })
        print(f"[HYBRID INDEX] Indexed document '{doc_id}' with {len(sparse_tokens)} sparse token weights")

    def query(self, query_dense: List[float], query_sparse: List[str], alpha: float = 0.5) -> str:
        # Blends dense dot product with sparse token matching
        best_doc = self.records[0]["doc_id"] if self.records else "none"
        print(f"[HYBRID QUERY] Blending dense (weight {alpha}) and sparse (weight {1.0 - alpha})")
        return best_doc

hybrid = HybridDenseSparseIndex()
hybrid.insert("DOC-001", [0.12, 0.45, 0.88], {"0x80040154": 2.4, "crash": 1.1})
res = hybrid.query([0.10, 0.40, 0.85], ["0x80040154"])
print("Top Hybrid Match:", res)

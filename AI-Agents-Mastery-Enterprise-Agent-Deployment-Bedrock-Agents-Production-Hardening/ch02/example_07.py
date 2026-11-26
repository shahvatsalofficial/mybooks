from typing import List, Dict, Any
import numpy as np

class VertexVectorSearchMemory:
    """Manages long-term vector embeddings for agent incident post-mortems."""

    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.memory_index: List[Dict[str, Any]] = []

    def mock_embed(self, text: str) -> List[float]:
        """Generates deterministic unit vector for mock testing."""
        np.random.seed(abs(hash(text)) % (2**31))
        vec = np.random.randn(self.dimension)
        return (vec / np.linalg.norm(vec)).tolist()

    def store_memory(self, doc_id: str, content: str, metadata: Dict[str, Any]) -> None:
        vector = self.mock_embed(content)
        self.memory_index.append({
            "id": doc_id,
            "content": content,
            "metadata": metadata,
            "vector": vector
        })

    def query_similar_memories(self, query_text: str, top_k: int = 2) -> List[Dict[str, Any]]:
        query_vec = np.array(self.mock_embed(query_text))
        scores = []
        for item in self.memory_index:
            target_vec = np.array(item["vector"])
            similarity = float(np.dot(query_vec, target_vec))
            scores.append((similarity, item))
            
        scores.sort(key=lambda x: x[0], reverse=True)
        return [{"score": s, "doc": item["content"], "metadata": item["metadata"]} for s, item in scores[:top_k]]

if __name__ == "__main__":
    mem = VertexVectorSearchMemory()
    mem.store_memory("PM-101", "GKE ingress gateway 502 Bad Gateway caused by Envoy upstream timeout.", {"env": "prod"})
    mem.store_memory("PM-102", "PostgreSQL connection exhaustion due to missing HikariCP pool limits.", {"env": "prod"})
    
    results = mem.query_similar_memories("Envoy ingress timeouts")
    print(f"Top memory match (Score: {results[0]['score']:.4f}): {results[0]['doc']}")

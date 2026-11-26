import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models

class LongTermMemoryManager:
    """
    Episodic & Semantic Long-Term Memory Manager using Qdrant Vector Store
    Supports importance weighting, recency decay, and hybrid retrieval.
    """
    def __init__(self, qdrant_url: str, collection_name: str = "agent_long_term_memory"):
        self.client = QdrantClient(url=qdrant_url)
        self.collection_name = collection_name
        self._ensure_collection()

    def _ensure_collection(self):
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in collections:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=1536, # OpenAI text-embedding-3-small dimension
                    distance=models.Distance.COSINE
                )
            )

    def store_memory(self, user_id: str, fact: str, vector: List[float], importance_score: float, memory_type: str = "semantic"):
        """Store an atomic fact with importance rating (0.0 - 1.0)."""
        point_id = hash(f"{user_id}:{fact}") % (2**63)
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "user_id": user_id,
                        "fact": fact,
                        "importance": importance_score,
                        "memory_type": memory_type,
                        "created_at": asyncio.get_event_loop().time(),
                        "access_count": 1
                    }
                )
            ]
        )

    def retrieve_memories(self, user_id: str, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve memories ranked by cosine similarity weighted by importance & recency."""
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=user_id)
                    )
                ]
            ),
            limit=top_k * 2
        )

        scored_memories = []
        now = asyncio.get_event_loop().time()

        for res in results:
            sim = res.score
            importance = res.payload.get("importance", 0.5)
            created_at = res.payload.get("created_at", now)
            
            # Recency decay formula: e^(-lambda * delta_t)
            age_days = (now - created_at) / 86400.0
            recency = np.exp(-0.05 * age_days)

            # Combined Score Formula: 0.5 * Sim + 0.3 * Importance + 0.2 * Recency
            final_score = (0.5 * sim) + (0.3 * importance) + (0.2 * recency)
            scored_memories.append({
                "fact": res.payload["fact"],
                "final_score": final_score,
                "importance": importance,
                "memory_type": res.payload["memory_type"]
            })

        scored_memories.sort(key=lambda x: x["final_score"], reverse=True)
        return scored_memories[:top_k]

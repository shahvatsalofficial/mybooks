# redis_semantic_cache.py — Enterprise Two-Tier FinOps Cache
import hashlib
import json
import time
from typing import Optional, Dict, Any, Tuple
import numpy as np

class RedisSemanticCache:
    """Production two-tier caching engine combining exact match and HNSW vector search."""
    def __init__(
        self,
        redis_client,
        similarity_threshold: float = 0.94,
        ttl_seconds: int = 604800 # 7 days
    ):
        self.redis = redis_client
        self.threshold = similarity_threshold
        self.ttl = ttl_seconds

    def _hash_query(self, prompt: str) -> str:
        """Deterministic SHA-256 hash for O(1) exact match lookup."""
        return hashlib.sha256(prompt.strip().lower().encode('utf-8')).hexdigest()

    async def get(self, prompt: str, prompt_vector: Optional[list] = None) -> Tuple[Optional[str], str]:
        """
        Retrieves cached response.
        Returns: (response_text, hit_type) where hit_type in ['EXACT', 'SEMANTIC', 'MISS']
        """
        # Tier 1: Exact Hash Match (< 1ms)
        h = self._hash_query(prompt)
        exact_hit = await self.redis.get(f"cache:exact:{h}")
        if exact_hit:
            return exact_hit.decode('utf-8'), "EXACT"

        # Tier 2: Semantic Vector Match (< 6ms)
        if prompt_vector is not None:
            # Execute Redis RediSearch vector query
            query_bytes = np.array(prompt_vector, dtype=np.float32).tobytes()
            # Redis HNSW query string searching for top 1 nearest neighbor
            q = (
                "*=>[KNN 1 @vector $vec AS score]"
            )
            params = {"vec": query_bytes}
            res = await self.redis.ft("idx:semantic_cache").search(q, query_params=params)

            if res.docs:
                top_doc = res.docs[0]
                cosine_sim = 1.0 - float(top_doc.score)
                if cosine_sim >= self.threshold:
                    return top_doc.response, "SEMANTIC"

        return None, "MISS"

    async def set(
        self,
        prompt: str,
        response: str,
        prompt_vector: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Stores response across both exact and vector cache tiers with sliding TTL."""
        h = self._hash_query(prompt)
        # Store exact match key
        await self.redis.setex(f"cache:exact:{h}", self.ttl, response)

        # Store semantic vector record
        if prompt_vector is not None:
            vec_bytes = np.array(prompt_vector, dtype=np.float32).tobytes()
            doc_id = f"cache:vector:{h}"
            mapping = {
                "prompt": prompt,
                "response": response,
                "vector": vec_bytes,
                "timestamp": int(time.time()),
                "metadata": json.dumps(metadata or {})
            }
            await self.redis.hset(doc_id, mapping=mapping)
            await self.redis.expire(doc_id, self.ttl)

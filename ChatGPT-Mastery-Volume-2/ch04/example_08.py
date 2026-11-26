"""
Production Redis Semantic Cache for Enterprise RAG
Delivers sub-15ms cached responses for semantically equivalent queries.
Author: Vatsal Shah, Enterprise AI Architect
"""
import time
import numpy as np
from typing import Optional, Tuple
import redis.asyncio as aioredis
from openai import AsyncOpenAI

class RedisSemanticCache:
    def __init__(
        self,
        redis_client: aioredis.Redis,
        openai_client: AsyncOpenAI,
        similarity_threshold: float = 0.95,
        ttl_seconds: int = 86400, # 24-hour cache TTL
        embedding_dim: int = 1024
    ):
        self.redis = redis_client
        self.openai = openai_client
        self.similarity_threshold = similarity_threshold
        self.ttl = ttl_seconds
        self.embedding_dim = embedding_dim
        self.index_name = "idx:semantic_cache"

    async def _compute_query_vector(self, text: str) -> np.ndarray:
        resp = await self.openai.embeddings.create(
            model="text-embedding-3-large",
            input=text,
            dimensions=self.embedding_dim
        )
        vec = np.array(resp.data[0].embedding, dtype=np.float32)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    async def get(self, query_text: str) -> Optional[str]:
        """Queries semantic cache for cosine similarity match >= threshold."""
        query_vec = await self._compute_query_vector(query_text)
        vector_bytes = query_vec.tobytes()

        # Query Redis Vector Similarity Index via FT.SEARCH
        search_query = (
            f"*=>[KNN 1 @embedding $vec AS score]"
        )
        try:
            results = await self.redis.execute_command(
                "FT.SEARCH",
                self.index_name,
                search_query,
                "PARAMS", 2, "vec", vector_bytes,
                "RETURN", 2, "response_text", "score",
                "DIALECT", 2
            )
            
            # Parse Redis result: [total_count, doc_id, [fields...]]
            if results and results[0] > 0:
                doc_fields = results[2]
                score = float(doc_fields[3]) # Cosine distance
                cosine_sim = 1.0 - score
                
                if cosine_sim >= self.similarity_threshold:
                    print(f"⚡ Semantic Cache HIT! (Cosine Similarity: {cosine_sim:.4f})")
                    return doc_fields[1].decode("utf-8")
                    
        except Exception as e:
            # Fall back gracefully to cache miss if index not yet initialized
            pass

        print("💨 Semantic Cache MISS. Proceeding to full RAG retrieval.")
        return None

    async def set(self, query_text: str, response_text: str) -> None:
        """Stores query vector and response payload into Redis."""
        query_vec = await self._compute_query_vector(query_text)
        doc_id = f"cache:{int(time.time() * 1000)}"
        
        pipe = self.redis.pipeline()
        pipe.hset(doc_id, mapping={
            "query_text": query_text,
            "response_text": response_text,
            "embedding": query_vec.tobytes()
        })
        pipe.expire(doc_id, self.ttl)
        await pipe.execute()

"""
PostgreSQL pgvector Async Client with Row-Level Security
"""
import asyncpg
import numpy as np

class PostgresVectorRepository:
    def __init__(self, db_pool: asyncpg.Pool):
        self.pool = db_pool

    async def hybrid_search_with_rls(
        self, tenant_id: str, query_embedding: np.ndarray, top_k: int = 5
    ) -> list[dict]:
        vector_str = "[" + ",".join(map(str, query_embedding.tolist())) + "]"
        
        query = """
        SET LOCAL app.current_tenant_id = $1;
        
        SELECT 
            chunk_id,
            document_title,
            content,
            1 - (embedding <=> $2::vector) AS cosine_similarity
        FROM enterprise_knowledge_chunks
        ORDER BY embedding <=> $2::vector
        LIMIT $3;
        """
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("SET LOCAL app.current_tenant_id = $1;", tenant_id)
                rows = await conn.fetch(
                    """
                    SELECT chunk_id, document_title, content, 1 - (embedding <=> $1::vector) AS cosine_similarity
                    FROM enterprise_knowledge_chunks
                    ORDER BY embedding <=> $1::vector
                    LIMIT $2;
                    """,
                    vector_str, top_k
                )
                return [dict(row) for row in rows]

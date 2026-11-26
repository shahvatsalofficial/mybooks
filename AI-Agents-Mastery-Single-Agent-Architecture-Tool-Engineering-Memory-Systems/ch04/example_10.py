class PostgresVectorMemoryStore:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

    def render_insert_sql(self, doc_id: str, content: str, embedding: List[float], metadata: Dict[str, Any]) -> Tuple[str, Tuple]:
        sql = """
            INSERT INTO episodic_memories (id, tenant_id, content, embedding, metadata, created_at)
            VALUES (%s, %s, %s, %s::vector, %s::jsonb, NOW());
        """
        return sql, (doc_id, self.tenant_id, content, str(embedding), json.dumps(metadata))

    def render_search_sql(self, query_embedding: List[float], top_k: int = 5, min_similarity: float = 0.75) -> Tuple[str, Tuple]:
        # Using pgvector cosine distance operator <=> where similarity = 1 - distance
        sql = """
            SELECT id, content, metadata, 1 - (embedding <=> %s::vector) AS similarity
            FROM episodic_memories
            WHERE tenant_id = %s AND (1 - (embedding <=> %s::vector)) >= %s
            ORDER BY embedding <=> %s::vector ASC
            LIMIT %s;
        """
        emb_str = str(query_embedding)
        return sql, (emb_str, self.tenant_id, emb_str, min_similarity, emb_str, top_k)

# Verification
pg_store = PostgresVectorMemoryStore(tenant_id="tenant_acme")
sample_emb = [0.12, 0.45, 0.78]
insert_query, insert_params = pg_store.render_insert_sql("doc_1", "Customer SLA policy", sample_emb, {"tier": "gold"})
search_query, search_params = pg_store.render_search_sql(sample_emb, top_k=3)
print("PostgreSQL RLS Vector Search Query Generated:")
print(search_query.strip()[:100] + "...")

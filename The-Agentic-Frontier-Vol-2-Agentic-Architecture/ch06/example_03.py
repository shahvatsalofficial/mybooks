class ParentDocumentRetriever:
    """
    Hierarchical Small-to-Big Retrieval System
    Search vector index on 128-token child chunks; return 2048-token parent documents.
    """
    def __init__(self, vector_store, doc_store):
        self.vector_store = vector_store
        self.doc_store = doc_store

    def retrieve(self, query_vector: List[float], top_k: int = 3) -> List[str]:
        # Search vector DB for top child chunks
        child_chunks = self.vector_store.search(query_vector, limit=top_k * 3)
        
        parent_ids = set()
        for chunk in child_chunks:
            parent_ids.add(chunk.payload["parent_id"])

        # Fetch full parent documents from document store
        parent_documents = [self.doc_store.get(p_id) for p_id in parent_ids]
        return parent_documents[:top_k]

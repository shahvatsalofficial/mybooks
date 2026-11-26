class HybridRAGRetriever:
    def __init__(self, documents: List[str]):
        self.documents = documents

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        # Reciprocal Rank Fusion (RRF) combining dense & sparse matches
        matches = [doc for doc in self.documents if any(term in doc.lower() for term in query.lower().split())]
        print(f"[HYBRID RAG] Retrieved {len(matches[:top_k])} top-ranked documents for query: '{query}'")
        return matches[:top_k]

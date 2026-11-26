from sentence_transformers import CrossEncoder

class TwoStageReRanker:
    """
    Cross-Encoder Re-Ranking Engine (BGE-Reranker-Large / Cohere-Rerank-v3)
    """
    def __init__(self, model_name: str = "BAAI/bge-reranker-large"):
        self.cross_encoder = CrossEncoder(model_name)

    def rerank(self, query: str, candidates: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        # Pair query with each candidate document
        query_doc_pairs = [[query, doc] for doc in candidates]
        
        # Predict cross-attention relevance scores
        scores = self.cross_encoder.predict(query_doc_pairs)
        
        ranked_results = []
        for doc, score in zip(candidates, scores):
            ranked_results.append({
                "document": doc,
                "relevance_score": float(score)
            })
            
        ranked_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return ranked_results[:top_k]

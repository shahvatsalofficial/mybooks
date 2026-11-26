from typing import Dict, Any

class SelfRAGReflectiveAgent:
    def __init__(self):
        self.threshold = 0.75

    def decide_if_retrieval_needed(self, user_query: str) -> bool:
        # Queries containing internal product terms require external retrieval
        needs = any(term in user_query.lower() for term in ["policy", "pricing", "cluster", "internal"])
        print(f"[SELF-RAG] Reflection on query '{user_query}': [RETRIEVE] = {needs}")
        return needs

    def critique_passage(self, passage: str, query: str) -> bool:
        # Verifies relevance score exceeds threshold
        score = 0.85 if "cluster" in passage.lower() else 0.40
        is_relevant = score >= self.threshold
        print(f"[SELF-RAG] Reflection on passage: [IS_REL] = {is_relevant} (Score: {score})")
        return is_relevant

rag = SelfRAGReflectiveAgent()
need = rag.decide_if_retrieval_needed("What is internal cluster retention policy?")
rel = rag.critique_passage("Cluster logs retained for 90 days in S3 Glacier", "retention policy")

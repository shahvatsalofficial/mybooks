class SemanticCompactor:
    def __init__(self, embedding_fn: Callable[[str], List[float]], max_tokens: int = 2048):
        self.embedding_fn = embedding_fn
        self.max_tokens = max_tokens
        self.messages: List[Dict[str, Any]] = []

    def score_relevance(self, query_emb: List[float], doc_emb: List[float]) -> float:
        dot_product = sum(a * b for a, b in zip(query_emb, doc_emb))
        norm_a = sum(a * a for a, b in zip(query_emb, doc_emb)) ** 0.5
        norm_b = sum(b * b for b in doc_emb) ** 0.5
        return dot_product / (norm_a * norm_b + 1e-9)

    def compact(self, user_goal: str) -> List[Dict[str, str]]:
        goal_emb = self.embedding_fn(user_goal)
        for msg in self.messages:
            if "emb" not in msg:
                msg["emb"] = self.embedding_fn(msg["content"])
            msg["score"] = self.score_relevance(goal_emb, msg["emb"])
        
        # Sort by relevance score descending and preserve top items within budget
        sorted_msgs = sorted(self.messages, key=lambda x: x["score"], reverse=True)
        retained = []
        accumulated_tokens = 0
        for m in sorted_msgs:
            t = len(m["content"]) // 4
            if accumulated_tokens + t <= self.max_tokens:
                retained.append(m)
                accumulated_tokens += t
        return [{"role": m["role"], "content": m["content"]} for m in sorted(retained, key=lambda x: x.get("timestamp", 0))]

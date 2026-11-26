import hashlib

class SemanticAgentCache:
    def __init__(self, embedding_fn: Callable[[str], List[float]], similarity_threshold: float = 0.92):
        self.exact_cache: Dict[str, str] = {}
        self.semantic_cache: List[Tuple[str, List[float], str]] = []
        self.embedding_fn = embedding_fn
        self.threshold = similarity_threshold

    def _hash_key(self, text: str) -> str:
        return hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()

    def get(self, query: str) -> Optional[str]:
        # Tier 1: Exact Hash Match (O(1) latency)
        key = self._hash_key(query)
        if key in self.exact_cache:
            return self.exact_cache[key]

        # Tier 2: Semantic Vector Match
        query_emb = self.embedding_fn(query)
        for _, cached_emb, cached_response in self.semantic_cache:
            dot = sum(a * b for a, b in zip(query_emb, cached_emb))
            norm_a = sum(a * a for a in query_emb) ** 0.5
            norm_b = sum(b * b for b in cached_emb) ** 0.5
            similarity = dot / (norm_a * norm_b + 1e-9)
            
            if similarity >= self.threshold:
                return cached_response
        return None

    def put(self, query: str, response: str):
        key = self._hash_key(query)
        self.exact_cache[key] = response
        emb = self.embedding_fn(query)
        self.semantic_cache.append((query, emb, response))

# Mock embedding verification
def mock_embed(text: str) -> List[float]:
    # Simple deterministic hash embedding for testing
    val = sum(ord(c) for c in text.lower())
    return [val % 10 / 10.0, (val * 2) % 10 / 10.0, (val * 3) % 10 / 10.0]

cache = SemanticAgentCache(embedding_fn=mock_embed, similarity_threshold=0.95)
cache.put("How do I rotate my API keys?", "Navigate to Settings -> API Keys -> Click Rotate.")
print("Cache Hit Query 1:", cache.get("How do I rotate my API keys?"))

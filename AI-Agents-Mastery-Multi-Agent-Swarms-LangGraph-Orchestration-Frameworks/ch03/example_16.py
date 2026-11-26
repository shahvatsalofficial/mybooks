class SubgraphSemanticCache:
    def __init__(self, ttl_seconds: int = 300):
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self.ttl = ttl_seconds

    def get_or_set(self, cache_key: str, compute_fn: Callable[[], Any]) -> Any:
        now = time.time()
        if cache_key in self._cache:
            created_at, val = self._cache[cache_key]
            if now - created_at < self.ttl:
                print(f"[SEMANTIC CACHE] HIT on '{cache_key}'! Zero LLM latency.")
                return val
                
        print(f"[SEMANTIC CACHE] MISS on '{cache_key}'. Computing and caching...")
        fresh_val = compute_fn()
        self._cache[cache_key] = (now, fresh_val)
        return fresh_val

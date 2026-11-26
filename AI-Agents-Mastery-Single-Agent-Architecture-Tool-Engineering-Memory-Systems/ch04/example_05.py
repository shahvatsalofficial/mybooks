class RedisDistributedMemory:
    def __init__(self, session_id: str, default_ttl_seconds: int = 3600):
        self.session_id = session_id
        self.ttl = default_ttl_seconds
        # Emulating Redis hash and list primitives
        self._mock_redis_store: Dict[str, List[str]] = {}

    def append_turn(self, role: str, content: str):
        key = f"agent_session:{self.session_id}:turns"
        payload = json.dumps({"role": role, "content": content, "timestamp": time.time()})
        if key not in self._mock_redis_store:
            self._mock_redis_store[key] = []
        self._mock_redis_store[key].append(payload)

    def fetch_recent_turns(self, count: int = 10) -> List[Dict[str, Any]]:
        key = f"agent_session:{self.session_id}:turns"
        raw_items = self._mock_redis_store.get(key, [])[-count:]
        return [json.loads(item) for item in raw_items]

# Verification
dist_mem = RedisDistributedMemory(session_id="sess_prod_4921")
dist_mem.append_turn("user", "Check cluster logs for node 4.")
dist_mem.append_turn("tool", "Node 4 CPU load at 94%. Memory at 82%.")
print("Redis Retrieved Turns:", len(dist_mem.fetch_recent_turns()))

import bisect

class ConsistentHashRing:
    def __init__(self, nodes: List[str], replicas: int = 3):
        self.replicas = replicas
        self.ring: Dict[int, str] = {}
        self.sorted_keys: List[int] = []

        for node in nodes:
            for i in range(replicas):
                val = f"{node}#{i}"
                h = int(hashlib.md5(val.encode()).hexdigest(), 16)
                self.ring[h] = node
                self.sorted_keys.append(h)
        self.sorted_keys.sort()

    def get_node(self, state_key: str) -> str:
        h = int(hashlib.md5(state_key.encode()).hexdigest(), 16)
        idx = bisect.bisect_right(self.sorted_keys, h)
        if idx == len(self.sorted_keys):
            idx = 0
        node = self.ring[self.sorted_keys[idx]]
        print(f"[HASH RING] Key '{state_key}' routed to shard '{node}'")
        return node

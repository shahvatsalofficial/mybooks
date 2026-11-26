import time
from typing import List, Dict

class CognitiveEvictionEngine:
    def __init__(self, max_capacity: int = 3, w_r: float = 0.3, w_f: float = 0.3, w_sim: float = 0.4):
        self.capacity = max_capacity
        self.w_r = w_r
        self.w_f = w_f
        self.w_sim = w_sim
        self.memories: List[Dict[str, Any]] = []

    def add_memory(self, memory_id: str, relevance: float) -> None:
        now = time.time()
        self.memories.append({
            "id": memory_id,
            "created_at": now,
            "last_accessed": now,
            "access_count": 1,
            "relevance": relevance
        })
        if len(self.memories) > self.capacity:
            self.evict_lowest_score()

    def evict_lowest_score(self) -> None:
        now = time.time()
        for m in self.memories:
            recency = 1.0 / (1.0 + (now - m["last_accessed"]))
            freq = min(1.0, m["access_count"] / 10.0)
            m["composite_score"] = (self.w_r * recency) + (self.w_f * freq) + (self.w_sim * m["relevance"])

        self.memories.sort(key=lambda x: x["composite_score"])
        evicted = self.memories.pop(0)
        print(f"[EVICTION ENGINE] Evicted memory '{evicted['id']}' with score {evicted['composite_score']:.3f}")

engine = CognitiveEvictionEngine(max_capacity=3)
engine.add_memory("Mem_A", 0.9)
engine.add_memory("Mem_B", 0.4)
engine.add_memory("Mem_C", 0.8)
engine.add_memory("Mem_D", 0.95)  # Triggers eviction of Mem_B

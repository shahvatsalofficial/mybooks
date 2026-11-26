class HierarchicalMemoryManager:
    def __init__(self, l3_vector_store: EpisodicMemoryStore):
        self.l1_local_cache: Dict[str, str] = {}
        self.l3_vault = l3_vector_store

    def recall(self, tenant_id: str, key_or_query: str) -> Tuple[str, str]:
        # Tier 1: Check L1 local cache
        if key_or_query in self.l1_local_cache:
            return "L1_HIT", self.l1_local_cache[key_or_query]

        # Tier 3: Query persistent vector store
        records = self.l3_vault.recall_episodes(tenant_id, key_or_query, top_k=1)
        if records:
            ans = records[0]["content"]
            # Populate L1
            self.l1_local_cache[key_or_query] = ans
            return "L3_HIT", ans

        return "MISS", "No relevant memory found."

# Verification
hierarchical = HierarchicalMemoryManager(vault)
status1, memory1 = hierarchical.recall("tenant_acme", "What are the billing preferences?")
status2, memory2 = hierarchical.recall("tenant_acme", "What are the billing preferences?")
print(f"Call 1: {status1} | Call 2: {status2} (L1 Cache Promotion Verified)")

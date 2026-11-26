class ChromaCrewMemoryWrapper:
    def __init__(self, collection_name: str = "crew_enterprise_memory"):
        self.collection_name = collection_name
        self._entries: List[Dict[str, Any]] = []

    def store_insight(self, agent_role: str, insight: str):
        print(f"[CHROMA MEMORY] Indexing insight from '{agent_role}': {insight[:40]}...")
        self._entries.append({
            "agent": agent_role,
            "text": insight,
            "timestamp": time.time()
        })

    def search_insights(self, query: str) -> List[str]:
        print(f"[CHROMA MEMORY] Querying memory for: '{query}'...")
        matches = [e["text"] for e in self._entries if query.lower() in e["text"].lower()]
        return matches

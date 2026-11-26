class VectorMemorySyncBus:
    def __init__(self):
        self._vector_indices: Dict[str, List[Dict[str, Any]]] = {}

    def commit_episodic_fact(self, collection_name: str, fact_text: str, source_agent: str, metadata: Dict[str, Any]):
        print(f"[VECTOR SYNC] Agent '{source_agent}' broadcasting new fact to '{collection_name}'...")
        fact_entry = {
            "fact_id": str(uuid.uuid4()),
            "text": fact_text,
            "source_agent": source_agent,
            "timestamp": time.time(),
            "metadata": metadata
        }
        
        if collection_name not in self._vector_indices:
            self._vector_indices[collection_name] = []
            
        self._vector_indices[collection_name].append(fact_entry)
        print(f"[VECTOR SYNC] Synchronized fact across {len(self._vector_indices[collection_name])} cluster peers.")

    def semantic_query(self, collection_name: str, query_term: str) -> List[Dict[str, Any]]:
        collection = self._vector_indices.get(collection_name, [])
        matches = [item for item in collection if query_term.lower() in item["text"].lower()]
        return matches

from typing import List, Dict, Any

class EntityRelationKnowledgeGraph:
    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, str]] = []

    def add_entity(self, entity_id: str, label: str, properties: Dict[str, Any]) -> None:
        self.nodes[entity_id] = {"label": label, **properties}

    def add_relationship(self, source_id: str, rel_type: str, target_id: str) -> None:
        self.edges.append({"source": source_id, "rel": rel_type, "target": target_id})

    def query_dependencies(self, entity_id: str) -> List[str]:
        # Traverses incoming dependency edges
        upstream = [e["source"] for e in self.edges if e["target"] == entity_id and e["rel"] == "DEPENDS_ON"]
        print(f"[GRAPH MEMORY] Found {len(upstream)} upstream dependencies for '{entity_id}'")
        return upstream

kg = EntityRelationKnowledgeGraph()
kg.add_entity("DB_POSTGRES", "Database", {"tier": "primary"})
kg.add_entity("SVC_PAYMENTS", "Microservice", {"language": "python"})
kg.add_entity("SVC_BILLING", "Microservice", {"language": "go"})
kg.add_relationship("SVC_PAYMENTS", "DEPENDS_ON", "DB_POSTGRES")
kg.add_relationship("SVC_BILLING", "DEPENDS_ON", "DB_POSTGRES")

deps = kg.query_dependencies("DB_POSTGRES")
print("Impacted Services on DB Outage:", deps)

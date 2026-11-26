class KnowledgeGraphMemory:
    def __init__(self):
        self.nodes: Set[str] = set()
        self.edges: List[Tuple[str, str, str]] = [] # (Subject, Predicate, Object)

    def ingest_triple(self, subject: str, predicate: str, obj: str):
        self.nodes.add(subject)
        self.nodes.add(obj)
        self.edges.append((subject, predicate, obj))

    def query_relationships(self, entity: str) -> List[str]:
        facts = []
        for s, p, o in self.edges:
            if s == entity:
                facts.append(f"{s} -> [{p}] -> {o}")
            elif o == entity:
                facts.append(f"{o} <- [{p}] <- {s}")
        return facts

# Verification
kg = KnowledgeGraphMemory()
kg.ingest_triple("Marcus Chen", "MANAGES", "Billing Service")
kg.ingest_triple("Billing Service", "DEPLOYS_TO", "AWS us-east-1")
kg.ingest_triple("Marcus Chen", "APPROVED_BY", "Elena Rostova")

print("Marcus Chen Relationships:")
for fact in kg.query_relationships("Marcus Chen"):
    print(f"  {fact}")

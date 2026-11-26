class GraphRAGMemory:
    def __init__(self):
        self.adjacency: Dict[str, Dict[str, str]] = {} # source -> {target: relation}

    def add_relationship(self, source: str, relation: str, target: str):
        if source not in self.adjacency:
            self.adjacency[source] = {}
        self.adjacency[source][target] = relation

    def find_path(self, start: str, end: str, max_depth: int = 3) -> Optional[List[str]]:
        queue = [[start]]
        visited = {start}
        
        while queue:
            path = queue.pop(0)
            node = path[-1]
            if node == end:
                return path
            if len(path) > max_depth:
                continue
                
            for neighbor in self.adjacency.get(node, {}):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])
        return None

# Verification
graph_rag = GraphRAGMemory()
graph_rag.add_relationship("Alice", "REPORTED_TO", "Bob")
graph_rag.add_relationship("Bob", "MANAGES", "Project Apollo")
graph_rag.add_relationship("Project Apollo", "USES_CLUSTER", "K8s-Prod-01")

print("Multi-Hop Path from Alice to Cluster:", graph_rag.find_path("Alice", "K8s-Prod-01"))

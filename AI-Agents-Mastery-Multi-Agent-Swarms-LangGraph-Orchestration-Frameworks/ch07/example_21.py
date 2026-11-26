class WaitForGraphDetector:
    def __init__(self):
        self.adjacency: Dict[str, set[str]] = {}

    def add_wait_edge(self, waiting_agent: str, holding_agent: str):
        if waiting_agent not in self.adjacency:
            self.adjacency[waiting_agent] = set()
        self.adjacency[waiting_agent].add(holding_agent)
        print(f"[WFG] Added edge: {waiting_agent} waits for {holding_agent}")

    def detect_cycle(self) -> Optional[List[str]]:
        visited = set()
        rec_stack = set()

        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)
            for neighbor in self.adjacency.get(node, []):
                if neighbor not in visited:
                    res = dfs(neighbor, path + [neighbor])
                    if res:
                        return res
                elif neighbor in rec_stack:
                    return path + [neighbor] # Cycle found!
            rec_stack.remove(node)
            return None

        for n in list(self.adjacency.keys()):
            if n not in visited:
                cycle = dfs(n, [n])
                if cycle:
                    print(f"[DEADLOCK ALERT] Cycle detected: {' -> '.join(cycle)}")
                    return cycle
        return None

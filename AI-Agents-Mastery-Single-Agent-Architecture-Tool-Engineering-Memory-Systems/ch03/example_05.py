class DynamicToolDiscoveryGateway:
    def __init__(self, embedding_fn: Callable[[str], List[float]], top_k: int = 4):
        self.embedding_fn = embedding_fn
        self.top_k = top_k
        self.tool_vault: List[Tuple[str, List[float], Dict[str, Any]]] = []

    def register_tool(self, name: str, description: str, tool_spec: Dict[str, Any]):
        emb = self.embedding_fn(description)
        self.tool_vault.append((name, emb, tool_spec))

    def discover_tools(self, current_thought_or_query: str) -> List[Dict[str, Any]]:
        query_emb = self.embedding_fn(current_thought_or_query)
        scored = []
        for name, emb, spec in self.tool_vault:
            dot = sum(a * b for a, b in zip(query_emb, emb))
            norm_a = sum(a * a for a in query_emb) ** 0.5
            norm_b = sum(b * b for b in emb) ** 0.5
            sim = dot / (norm_a * norm_b + 1e-9)
            scored.append((sim, spec))

        # Sort descending and return top K tool specifications
        scored.sort(key=lambda x: x[0], reverse=True)
        return [spec for _, spec in scored[:self.top_k]]

# Verification
def mock_tool_embed(text: str) -> List[float]:
    v = sum(ord(c) for c in text.lower())
    return [v % 7 / 7.0, (v * 3) % 7 / 7.0, (v * 5) % 7 / 7.0]

discovery = DynamicToolDiscoveryGateway(embedding_fn=mock_tool_embed, top_k=2)
discovery.register_tool("query_sql", "Query operational PostgreSQL database tables", {"name": "query_sql"})
discovery.register_tool("send_slack", "Post an alert message to an internal team Slack channel", {"name": "send_slack"})
discovery.register_tool("fetch_k8s_logs", "Inspect container pod logs in Kubernetes", {"name": "fetch_k8s_logs"})

active_tools = discovery.discover_tools("The cluster node is failing, check container logs")
print(f"Dynamically Discovered Tools ({len(active_tools)} bound):", [t["name"] for t in active_tools])

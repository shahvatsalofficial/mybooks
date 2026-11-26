class DynamicSubgraphRegistry:
    def __init__(self):
        self._subgraphs: Dict[str, Any] = {}

    def register_subgraph(self, domain_name: str, compiled_graph: Any):
        print(f"[REGISTRY] Registering domain subgraph: '{domain_name}'")
        self._subgraphs[domain_name] = compiled_graph

    def get_subgraph(self, domain_name: str) -> Any:
        if domain_name not in self._subgraphs:
            raise KeyError(f"Requested domain subgraph '{domain_name}' is not registered.")
        return self._subgraphs[domain_name]

    def hot_reload(self, domain_name: str, new_compiled_graph: Any):
        print(f"[REGISTRY] Hot-reloading active instance of '{domain_name}'...")
        self._subgraphs[domain_name] = new_compiled_graph

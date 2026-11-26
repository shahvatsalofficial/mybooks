class MockPregelEngine:
    def __init__(self, nodes: Dict[str, Callable], reducers: Dict[str, Callable]):
        self.nodes = nodes
        self.reducers = reducers
        self.step_counter = 0

    def execute_superstep(self, current_state: Dict[str, Any], active_nodes: List[str]) -> Dict[str, Any]:
        self.step_counter += 1
        print(f"\n[PREGEL SUPERSTEP {self.step_counter}] Executing {len(active_nodes)} nodes concurrently: {active_nodes}...")
        
        # 1. Parallel execution barrier
        updates: List[Dict[str, Any]] = []
        for node_name in active_nodes:
            fn = self.nodes[node_name]
            delta = fn(current_state)
            updates.append(delta)
            
        # 2. Sequential Reducer Consolidation Barrier
        new_state = current_state.copy()
        for delta in updates:
            for k, val in delta.items():
                if k in self.reducers:
                    new_state[k] = self.reducers[k](new_state.get(k), val)
                else:
                    new_state[k] = val
                    
        print(f"[PREGEL SUPERSTEP {self.step_counter}] State barrier synchronized. Next step ready.")
        return new_state

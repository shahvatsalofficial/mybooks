class AgentStateDict(TypedDict):
    input: str
    intermediate_steps: List[str]
    final_answer: Optional[str]

class MinimalLangGraphEngine:
    def __init__(self):
        self.nodes: Dict[str, Callable[[AgentStateDict], AgentStateDict]] = {}
        self.edges: Dict[str, Callable[[AgentStateDict], str]] = {}

    def add_node(self, name: str, func: Callable[[AgentStateDict], AgentStateDict]):
        self.nodes[name] = func

    def add_conditional_edge(self, from_node: str, router: Callable[[AgentStateDict], str]):
        self.edges[from_node] = router

    def execute(self, initial_state: AgentStateDict, start_node: str, max_iterations: int = 5) -> AgentStateDict:
        state = dict(initial_state)
        current = start_node
        
        for _ in range(max_iterations):
            state = self.nodes[current](state)
            if current in self.edges:
                next_node = self.edges[current](state)
                if next_node == "__end__":
                    break
                current = next_node
            else:
                break
        return state

# Verification
def node_reason(s: AgentStateDict) -> AgentStateDict:
    s["intermediate_steps"].append("Reasoning step performed.")
    return s

def router_check(s: AgentStateDict) -> str:
    return "__end__" if len(s["intermediate_steps"]) >= 2 else "reason"

graph = MinimalLangGraphEngine()
graph.add_node("reason", node_reason)
graph.add_conditional_edge("reason", router_check)

final_st = graph.execute({"input": "audit", "intermediate_steps": [], "final_answer": None}, start_node="reason")
print("LangGraph Execution State Steps:", len(final_st["intermediate_steps"]))

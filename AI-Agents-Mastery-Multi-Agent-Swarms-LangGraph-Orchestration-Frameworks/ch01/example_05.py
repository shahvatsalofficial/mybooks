class AgentCapability(BaseModel):
    name: str
    tags: List[str]
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    avg_latency_ms: float = 100.0
    reliability_score: float = 1.0

class DynamicSwarmRegistry:
    def __init__(self):
        self._registry: Dict[str, Tuple[AgentProtocol, AgentCapability]] = {}

    def register(self, agent: AgentProtocol, capability: AgentCapability):
        self._registry[agent.name] = (agent, capability)

    def find_best_agent(self, required_tags: List[str]) -> Optional[AgentProtocol]:
        best_agent = None
        highest_score = -1.0
        
        for name, (agent, cap) in self._registry.items():
            matching_tags = set(required_tags).intersection(set(cap.tags))
            if not matching_tags:
                continue
            # Score formula: tag match ratio * reliability score
            score = (len(matching_tags) / len(required_tags)) * cap.reliability_score
            if score > highest_score:
                highest_score = score
                best_agent = agent
                
        return best_agent

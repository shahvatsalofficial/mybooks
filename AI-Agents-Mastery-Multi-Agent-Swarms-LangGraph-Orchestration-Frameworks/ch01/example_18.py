class AgentHeartbeatRecord(BaseModel):
    agent_id: str
    last_heartbeat_timestamp: float
    current_workload_capacity: int
    is_active: bool = True

class SwarmLivenessMonitor:
    def __init__(self, timeout_threshold_sec: float = 5.0):
        self.timeout_threshold = timeout_threshold_sec
        self.registry: Dict[str, AgentHeartbeatRecord] = {}

    def heartbeat(self, agent_id: str, capacity: int = 10):
        self.registry[agent_id] = AgentHeartbeatRecord(
            agent_id=agent_id,
            last_heartbeat_timestamp=time.time(),
            current_workload_capacity=capacity
        )

    def detect_and_cull_dead_agents(self) -> List[str]:
        now = time.time()
        dead_agents = []
        for aid, record in self.registry.items():
            if now - record.last_heartbeat_timestamp > self.timeout_threshold:
                record.is_active = False
                dead_agents.append(aid)
                print(f"[LIVENESS ALERT] Agent '{aid}' missed heartbeat! Dead after {now - record.last_heartbeat_timestamp:.2f}s.")
        return dead_agents

class IntelligentSupervisor:
    def __init__(self, registry: DynamicSwarmRegistry):
        self.registry = registry
        self.audit_log: List[Dict[str, Any]] = []

    def route_and_execute(self, required_tags: List[str], task_payload: str) -> AgentMessage:
        agent = self.registry.find_best_agent(required_tags)
        if not agent:
            raise RuntimeError(f"No suitable agent found for capability tags: {required_tags}")
        
        msg = AgentMessage(
            sender="IntelligentSupervisor",
            sender_role=AgentRole.SUPERVISOR,
            recipient=agent.name,
            message_type=MessageType.TASK_ASSIGNMENT,
            content=task_payload
        )
        t0 = time.time()
        response = agent.process_message(msg)
        elapsed = (time.time() - t0) * 1000
        
        self.audit_log.append({
            "target_agent": agent.name,
            "tags": required_tags,
            "latency_ms": elapsed,
            "status": "COMPLETED"
        })
        return response

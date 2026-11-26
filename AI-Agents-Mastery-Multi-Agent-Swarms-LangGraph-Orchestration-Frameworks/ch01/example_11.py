class HandoffCommand(BaseModel):
    target_agent: str
    target_role: AgentRole
    context_payload: Dict[str, Any]
    handoff_reason: str
    audit_trail: List[str] = Field(default_factory=list)

class HandoffRouter:
    def __init__(self, agents: Dict[str, AgentProtocol]):
        self.agents = agents
        self.active_agent: AgentProtocol = agents["IntakeAgent"]

    def execute_handoff(self, command: HandoffCommand) -> AgentMessage:
        if command.target_agent not in self.agents:
            raise KeyError(f"Target handoff agent '{command.target_agent}' not registered in swarm.")
        
        print(f"[HANDOFF] Transferring context from '{self.active_agent.name}' to '{command.target_agent}'...")
        print(f"[REASON] {command.handoff_reason}")
        
        command.audit_trail.append(f"Handoff to {command.target_agent} at {time.time()}")
        self.active_agent = self.agents[command.target_agent]
        
        # Dispatch migrated context to target agent
        envelope = AgentMessage(
            sender="HandoffDispatcher",
            sender_role=AgentRole.SUPERVISOR,
            recipient=self.active_agent.name,
            message_type=MessageType.TASK_ASSIGNMENT,
            content=json.dumps(command.context_payload),
            metadata={"audit_trail": command.audit_trail}
        )
        return self.active_agent.process_message(envelope)

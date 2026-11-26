class HardenedAgentEnvelope(BaseModel):
    root_trace_id: str
    parent_span_id: Optional[str]
    current_depth: int = Field(ge=0, le=5, description="Max recursion depth is hardcoded to 5")
    ttl: int = Field(ge=1, le=10, description="Max remaining agent hops")
    sender: str
    recipient: str
    payload: Dict[str, Any]

    def spawn_child_hop(self, next_recipient: str, new_payload: Dict[str, Any]) -> HardenedAgentEnvelope:
        if self.ttl <= 1:
            raise PermissionError(f"Agent hop TTL expired! Cannot delegate further from {self.sender} to {next_recipient}.")
        if self.current_depth >= 5:
            raise PermissionError(f"Maximum recursion depth of 5 exceeded at agent {self.sender}.")

        return HardenedAgentEnvelope(
            root_trace_id=self.root_trace_id,
            parent_span_id=str(uuid.uuid4()),
            current_depth=self.current_depth + 1,
            ttl=self.ttl - 1,
            sender=self.recipient,
            recipient=next_recipient,
            payload=new_payload
        )

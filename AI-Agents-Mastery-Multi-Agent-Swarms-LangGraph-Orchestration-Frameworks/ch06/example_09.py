class SchemaTransformer:
    @staticmethod
    def langgraph_to_a2a(state_delta: Dict[str, Any], conversation_id: str) -> A2AMessageEnvelope:
        routing = A2ARoutingHeader(
            conversation_id=conversation_id,
            root_trace_id=str(uuid.uuid4()),
            sender_uri="urn:agent:langgraph_runner",
            recipient_uri="urn:agent:external_crew"
        )
        sec = A2ACryptoEngine.sign_payload(routing, state_delta)
        return A2AMessageEnvelope(
            routing=routing,
            security=sec,
            intent="TASK_REQUEST",
            payload=state_delta
        )

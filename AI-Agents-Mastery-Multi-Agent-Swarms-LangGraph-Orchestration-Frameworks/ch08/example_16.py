class OpenInferenceSpanSerializer:
    @staticmethod
    def serialize_agent_span(span_name: str, agent_role: str, inputs: Dict[str, Any], outputs: Dict[str, Any], tokens: int) -> Dict[str, Any]:
        return {
            "name": span_name,
            "context": {
                "span_id": str(uuid.uuid4()),
                "trace_id": str(uuid.uuid4())
            },
            "attributes": {
                "openinference.span.kind": "AGENT",
                "agent.role": agent_role,
                "llm.token_count.total": tokens,
                "input.value": json.dumps(inputs),
                "output.value": json.dumps(outputs)
            }
        }

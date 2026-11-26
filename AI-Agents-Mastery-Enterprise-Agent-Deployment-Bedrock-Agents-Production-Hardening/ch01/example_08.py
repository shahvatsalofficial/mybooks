from typing import Dict, Any

class BedrockTraceDecoder:
    """Parses raw Bedrock agent trace events into structured telemetry spans."""

    @staticmethod
    def decode_trace_event(trace_data: Dict[str, Any]) -> Dict[str, Any]:
        trace = trace_data.get("trace", {})
        span_info = {"type": "UNKNOWN", "details": {}}
        
        if "orchestrationTrace" in trace:
            orch = trace["orchestrationTrace"]
            if "rationale" in orch:
                span_info = {
                    "type": "RATIONALE",
                    "thought": orch["rationale"].get("text", "")
                }
            elif "invocationInput" in orch:
                inv = orch["invocationInput"]
                span_info = {
                    "type": "TOOL_INVOCATION",
                    "action_group": inv.get("actionGroupInvocationInput", {}).get("actionGroupName", ""),
                    "api_path": inv.get("actionGroupInvocationInput", {}).get("apiPath", ""),
                    "parameters": inv.get("actionGroupInvocationInput", {}).get("parameters", [])
                }
            elif "observation" in orch:
                obs = orch["observation"]
                span_info = {
                    "type": "OBSERVATION",
                    "status": obs.get("actionGroupInvocationOutput", {}).get("httpStatusCode", 200),
                    "raw_output": obs.get("actionGroupInvocationOutput", {}).get("text", "")[:100]
                }
        return span_info

if __name__ == "__main__":
    mock_trace = {
        "trace": {
            "orchestrationTrace": {
                "rationale": {"text": "I need to query CloudWatch logs to diagnose the database latency spike."}
            }
        }
    }
    decoded = BedrockTraceDecoder.decode_trace_event(mock_trace)
    print("-> Decoded Trace Event:")
    print(f"   Type: {decoded['type']}")
    print(f"   Thought: {decoded['thought']}")

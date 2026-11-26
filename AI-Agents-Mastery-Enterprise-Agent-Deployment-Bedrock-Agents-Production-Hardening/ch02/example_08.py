import json
import time
from typing import Generator

def stream_agent_events(user_input: str) -> Generator[str, None, None]:
    """Simulates production SSE generator emitting thoughts, tool calls, and tokens."""
    yield f"data: {json.dumps({'event': 'thought', 'content': 'Analyzing system telemetry for anomalies...'})}\n\n"
    time.sleep(0.05)
    
    yield f"data: {json.dumps({'event': 'tool_call', 'tool': 'query_prometheus', 'args': {'cluster': 'prod-us-1'}})}\n\n"
    time.sleep(0.05)
    
    yield f"data: {json.dumps({'event': 'tool_result', 'status': 'OK', 'cpu_percent': 94.2})}\n\n"
    time.sleep(0.05)
    
    answer_tokens = ["Cluster ", "prod-us-1 ", "exhibits ", "abnormal ", "CPU ", "saturation ", "(94.2%)."]
    for tok in answer_tokens:
        yield f"data: {json.dumps({'event': 'token', 'text': tok})}\n\n"
        time.sleep(0.02)
        
    yield f"data: {json.dumps({'event': 'done', 'duration_ms': 342})}\n\n"

if __name__ == "__main__":
    events = list(stream_agent_events("Check cluster health"))
    print(f"Generated {len(events)} streaming SSE events successfully.")

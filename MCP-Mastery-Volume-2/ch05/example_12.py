"""
Real-Time Event Multiplexer for LangGraph & MCP Streaming
Author: Vatsal Shah | Vatsal Shah
Runtime: Python 3.11+ with FastAPI & LangGraph
"""

import json
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI(title="LangGraph-MCP-Streaming-Gateway")

async def event_generator(graph, user_prompt: str, thread_id: str) -> AsyncGenerator[str, None]:
    """Yield SSE formatted events for client consumption."""
    inputs = {"messages": [{"role": "user", "content": user_prompt}]}
    config = {"configurable": {"thread_id": thread_id}}

    async for event in graph.astream_events(inputs, config=config, version="v2"):
        kind = event["event"]

        # Stream individual LLM tokens in real-time
        if kind == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            if hasattr(chunk, "content") and chunk.content:
                payload = json.dumps({"type": "token", "content": chunk.content})
                yield f"data: {payload}\n\n"

        # Stream Tool Execution Start
        elif kind == "on_tool_start":
            tool_name = event.get("name", "unknown_tool")
            inputs_data = event["data"].get("input", {})
            payload = json.dumps({"type": "tool_start", "tool": tool_name, "input": inputs_data})
            yield f"data: {payload}\n\n"

        # Stream Tool Execution Completion
        elif kind == "on_tool_end":
            tool_name = event.get("name", "unknown_tool")
            output_data = str(event["data"].get("output", ""))
            payload = json.dumps({"type": "tool_end", "tool": tool_name, "output": output_data[:200]})
            yield f"data: {payload}\n\n"

    yield "data: {\"type\": \"done\"}\n\n"

@app.post("/api/v1/chat/stream")
async def chat_stream_endpoint(prompt: str, thread_id: str):
    """HTTP POST endpoint returning live SSE stream."""
    # Assume `compiled_graph` is injected or imported
    from my_graph_module import compiled_graph
    return StreamingResponse(
        event_generator(compiled_graph, prompt, thread_id),
        media_type="text/event-stream"
    )

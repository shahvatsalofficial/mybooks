"""
Recipe 03.5: High-Concurrency WebSocket-to-SSE Streaming Bridge
Author: Vatsal Shah (Opportunity4u Press)
License: Apache-2.0
"""

import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import httpx

app = FastAPI(title="WebSocket Claude Bridge")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # Await client prompt initiation
        init_data = await websocket.receive_text()
        request_payload = json.loads(init_data)
        user_prompt = request_payload.get("prompt", "")

        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            "accept": "text/event-stream"
        }
        body = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 2048,
            "stream": True,
            "messages": [{"role": "user", "content": user_prompt}]
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", "https://api.anthropic.com/v1/messages", headers=headers, json=body) as upstream:
                async for line in upstream.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            event = json.loads(data_str)
                            if event.get("type") == "content_block_delta":
                                delta = event.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    # Send atomic token frame over WebSocket
                                    await websocket.send_json({
                                        "type": "token",
                                        "text": delta.get("text", "")
                                    })
                        except json.JSONDecodeError:
                            continue

        await websocket.send_json({"type": "complete"})
        await websocket.close()

    except WebSocketDisconnect:
        # Client disconnected early - cleanly terminate upstream connection
        pass

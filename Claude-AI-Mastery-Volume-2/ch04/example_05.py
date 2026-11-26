"""
Recipe 04.4: High-Availability Stateless MCP SSE Gateway with Redis Backplane
Author: Vatsal Shah (Opportunity4u Press)
License: Apache-2.0
"""

import os
import json
import asyncio
import uuid
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException
from sse_starlette.sse import EventSourceResponse
import redis.asyncio as aioredis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MCPStatelessGateway")

app = FastAPI(title="Stateless Enterprise MCP Gateway")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)

# Channel naming convention: mcp:session:{session_id}:outbox
def get_session_channel(session_id: str) -> str:
    return f"mcp:session:{session_id}:outbox"

@app.get("/sse")
async def sse_handshake(request: Request):
    """Establishes persistent SSE connection; subscribes to dedicated Redis session channel."""
    session_id = str(uuid.uuid4())
    logger.info(f"Establishing SSE connection for Session ID: {session_id}")

    async def event_generator():
        # First event: Send endpoint URI containing session identifier
        endpoint_event = {
            "event": "endpoint",
            "data": f"/messages?sessionId={session_id}"
        }
        yield endpoint_event

        # Subscribe to session outbox channel in Redis
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(get_session_channel(session_id))

        try:
            while True:
                # Disconnect if client drops connection
                if await request.is_disconnected():
                    logger.info(f"Client disconnected for session {session_id}")
                    break

                # Poll Redis pubsub with timeout for heartbeat
                try:
                    message = await asyncio.wait_for(
                        pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0),
                        timeout=15.0
                    )
                    if message and message["type"] == "message":
                        yield {
                            "event": "message",
                            "data": message["data"]
                        }
                except asyncio.TimeoutError:
                    # Emit SSE comment heartbeat to keep intermediate ALB / CDN proxies alive
                    yield {":": "keepalive"}

        finally:
            await pubsub.unsubscribe(get_session_channel(session_id))
            await pubsub.close()
            logger.info(f"Cleaned up Redis subscriptions for session {session_id}")

    return EventSourceResponse(event_generator())

@app.post("/messages")
async def handle_message_dispatch(request: Request, sessionId: str):
    """Receives JSON-RPC request from any pod and publishes response to session outbox channel."""
    if not sessionId:
        raise HTTPException(status_code=400, detail="Missing required 'sessionId' query parameter.")

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload.")

    req_id = body.get("id")
    method = body.get("method")
    logger.info(f"Dispatching method '{method}' for session {sessionId} (Req ID: {req_id})")

    # Execute tool logic (or route to worker queue)
    if method == "tools/list":
        result_payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "query_inventory",
                        "description": "Returns warehouse stock levels across fulfillment centers.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"sku": {"type": "string"}},
                            "required": ["sku"]
                        }
                    }
                ]
            }
        }
    elif method == "tools/call":
        sku = body.get("params", {}).get("arguments", {}).get("sku", "UNKNOWN")
        result_payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": f"SKU {sku}: 4,280 units available in US-East."}]
            }
        }
    else:
        result_payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method '{method}' not implemented."}
        }

    # Publish result to Redis session channel - automatically routed to the pod holding the SSE socket
    await redis_client.publish(get_session_channel(sessionId), json.dumps(result_payload))
    return {"status": "ACCEPTED", "sessionId": sessionId}

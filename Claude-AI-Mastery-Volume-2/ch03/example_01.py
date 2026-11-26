"""
Recipe 03.1: Hardened Python SSE Streaming Gateway
Author: Vatsal Shah (Opportunity4u Press)
License: Apache-2.0
"""

import os
import json
import asyncio
import logging
from typing import AsyncGenerator
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("StreamingGateway")

app = FastAPI(title="Claude SSE Enterprise Gateway", version="1.0.0")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
UPSTREAM_URL = "https://api.anthropic.com/v1/messages"

async def claude_stream_generator(prompt: str, model: str = "claude-3-5-sonnet-20241022") -> AsyncGenerator[str, None]:
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
        "accept": "text/event-stream"
    }
    payload = {
        "model": model,
        "max_tokens": 4096,
        "stream": True,
        "messages": [{"role": "user", "content": prompt}]
    }

    # Bounded queue to regulate memory and enforce backpressure
    chunk_queue: asyncio.Queue = asyncio.Queue(maxsize=100)

    async def heartbeat_sender():
        """Emits synthetic SSE comments every 15s to keep proxy connections alive."""
        while True:
            await asyncio.sleep(15.0)
            await chunk_queue.put(": ping - heartbeat keepalive\n\n")

    heartbeat_task = asyncio.create_task(heartbeat_sender())

    async def fetch_upstream():
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
                async with client.stream("POST", UPSTREAM_URL, headers=headers, json=payload) as response:
                    if response.status_code != 200:
                        err_body = await response.aread()
                        await chunk_queue.put(f"event: error\ndata: {json.dumps({'error': err_body.decode()})}\n\n")
                        return

                    async for line in response.aiter_lines():
                        if line:
                            # Forward raw SSE lines
                            await chunk_queue.put(f"{line}\n")
                        else:
                            await chunk_queue.put("\n")
        except Exception as exc:
            logger.error(f"Upstream stream failure: {exc}")
            await chunk_queue.put(f"event: error\ndata: {json.dumps({'error': str(exc)})}\n\n")
        finally:
            await chunk_queue.put(None) # Sentinel to signal completion

    producer_task = asyncio.create_task(fetch_upstream())

    try:
        while True:
            # Yield chunks to client as they arrive
            chunk = await chunk_queue.get()
            if chunk is None:
                break
            yield chunk
            chunk_queue.task_done()
    finally:
        heartbeat_task.cancel()
        producer_task.cancel()

@app.post("/v1/chat/stream")
async def chat_stream_endpoint(request: Request):
    data = await request.json()
    prompt = data.get("prompt")
    if not prompt:
        raise HTTPException(status_code=400, detail="Missing required 'prompt' field.")

    return StreamingResponse(
        claude_stream_generator(prompt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no" # Prevents NGINX from buffering SSE stream
        }
    )

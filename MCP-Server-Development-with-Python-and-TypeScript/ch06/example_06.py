from contextlib import asynccontextmanager
from typing import AsyncIterator
from mcp.server.fastmcp import FastMCP, Context
import httpx

@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[dict]:
    """Manages global resource pools across the server's operational lifetime."""
    # STARTUP: Initialize persistent HTTP client session
    http_client = httpx.AsyncClient(timeout=30.0)
    try:
        # Yield shared resources to active server context
        yield {
            "http_client": http_client,
            "version": "1.0.0"
        }
    finally:
        # TEARDOWN: Ensure socket closure on process shutdown
        await http_client.aclose()

mcp = FastMCP("LifespanServer", lifespan=server_lifespan)

@mcp.tool()
async def fetch_weather(city: str, ctx: Context) -> str:
    """Queries current weather using the shared lifespan HTTP client."""
    # Extract shared resource pool from injected context
    client: httpx.AsyncClient = ctx.request_context.lifespan_context["http_client"]
    resp = await client.get(f"https://wttr.in/{city}?format=j1")
    return resp.text[:200]

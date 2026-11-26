from contextlib import asynccontextmanager, AsyncExitStack
import asyncpg
import redis.asyncio as aioredis
import httpx
from mcp.server.fastmcp import FastMCP

@asynccontextmanager
async def enterprise_lifespan(server: FastMCP):
    """Coordinates multiple heterogeneous network connections atomically."""
    async with AsyncExitStack() as stack:
        # 1. Initialize PostgreSQL Connection Pool
        db_pool = await stack.enter_async_context(
            asyncpg.create_pool("postgresql://app:secret@db:5432/analytics", min_size=5, max_size=20)
        )
        
        # 2. Initialize Redis Connection Client
        redis_client = await stack.enter_async_context(
            aioredis.from_url("redis://cache:6379/0", decode_responses=True)
        )
        
        # 3. Initialize Shared HTTP Client Session
        http_client = await stack.enter_async_context(
            httpx.AsyncClient(timeout=15.0)
        )
        
        # Yield all active resource handles to server context
        yield {
            "db": db_pool,
            "redis": redis_client,
            "http": http_client
        }
        # When execution leaves this block (process termination or error),
        # AsyncExitStack unwinds the stack in reverse order (LIFO),
        # guaranteeing clean closure of http, redis, and db_pool!

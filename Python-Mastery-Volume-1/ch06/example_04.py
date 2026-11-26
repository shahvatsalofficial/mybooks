"""
Recipe 06.2: Resilient HTTP/2 Streaming Client
File: recipe_06_2_http2_pool_client.py
Python Version: 3.12+
"""

from __future__ import annotations
import asyncio
import httpx
import logging
import random
import time
from typing import AsyncGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("HTTP2Client")


class ResilientHTTP2Client:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        
        # Configure Bounded Connection Pool Limits
        limits = httpx.Limits(
            max_connections=100,           # Strict cap to prevent socket exhaustion
            max_keepalive_connections=25,  # Reusable persistent sockets
            keepalive_expiry=25.0,         # Safely below cloud 30s idle timeout
        )
        
        # Configure Strict Per-Phase Timeouts
        timeout = httpx.Timeout(
            connect=3.0,  # Max time for TCP + TLS handshake
            read=10.0,    # Max time waiting for next stream packet
            write=5.0,    # Max time flushing data to socket
            pool=2.0,     # Max time waiting for available connection from pool
        )
        
        # HTTP/2 Client Instance (Shared singleton)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            http2=True,           # Enforce HTTP/2 binary framing & multiplexing
            limits=limits,
            timeout=timeout,
        )

    async def close(self) -> None:
        await self.client.aclose()
        logger.info("HTTP/2 connection pool closed.")

    async def fetch_with_retry(
        self,
        endpoint: str,
        max_retries: int = 3,
        base_backoff: float = 0.25,
    ) -> dict:
        """Executes HTTP/2 request with exponential jittered backoff."""
        for attempt in range(1, max_retries + 1):
            start = time.perf_counter()
            try:
                response = await self.client.get(endpoint)
                response.raise_for_status()
                
                latency = (time.perf_counter() - start) * 1000
                logger.info(f"[{response.http_version}] {endpoint} resolved in {latency:.2f}ms")
                return response.json()

            except (httpx.ConnectError, httpx.PoolTimeout, httpx.HTTPStatusError) as exc:
                logger.warning(f"Attempt {attempt}/{max_retries} failed for {endpoint}: {exc}")
                if attempt == max_retries:
                    raise

                # Full jitter backoff formula: sleep = rand(0, base * 2^attempt)
                backoff = random.uniform(0, base_backoff * (2 ** attempt))
                await asyncio.sleep(backoff)

        raise RuntimeError("Retries exhausted.")

    async def stream_large_dataset(self, endpoint: str) -> AsyncGenerator[bytes, None]:
        """Streams large binary datasets with zero in-memory accumulation."""
        async with self.client.stream("GET", endpoint) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes(chunk_size=65536):
                yield chunk


async def test_client_execution() -> None:
    # Point to mock or production HTTP/2 endpoint
    client = ResilientHTTP2Client("https://httpbin.org")
    try:
        # Execute concurrent multiplexed requests over single TCP socket
        async with asyncio.TaskGroup() as tg:
            t1 = tg.create_task(client.fetch_with_retry("/get?stream=1"))
            t2 = tg.create_task(client.fetch_with_retry("/get?stream=2"))
            t3 = tg.create_task(client.fetch_with_retry("/get?stream=3"))

        logger.info("All 3 HTTP/2 multiplexed streams completed successfully.")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_client_execution())

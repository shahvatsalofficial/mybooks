# Offloading synchronous blocking operations to an isolated worker thread
import asyncio
import requests

async def fetch_legacy_telemetry(url: str) -> dict:
    # Safely executes synchronous requests.get() inside a thread pool,
    # freeing the event loop to continue serving concurrent HTTP transactions.
    response = await asyncio.to_thread(requests.get, url, timeout=5.0)
    return response.json()

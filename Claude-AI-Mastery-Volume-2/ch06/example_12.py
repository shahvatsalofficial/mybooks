# Production Remediation: Non-blocking Async HTTP client with strict connection limits
import httpx

# Shared client initialized in lifespan
client = httpx.AsyncClient(
    timeout=httpx.Timeout(5.0, connect=2.0),
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
)

@mcp.tool()
async def fetch_upstream_metrics(url: str) -> str:
    """Fetches remote cluster metrics asynchronously without blocking the event loop."""
    response = await client.get(url)
    response.raise_for_status()
    return response.text

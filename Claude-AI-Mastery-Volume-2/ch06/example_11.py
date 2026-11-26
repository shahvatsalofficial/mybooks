# FATAL FLAW: Blocking synchronous I/O executed inside async def coroutine
@mcp.tool()
async def fetch_upstream_metrics(url: str) -> str:
    return requests.get(url, timeout=10.0).text

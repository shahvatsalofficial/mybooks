# Production Patch: Dedicated Capacity Limiters & Asynchronous DB Access
import anyio
import asyncpg

# Dedicated limiter for CPU-intensive mathematical tasks
CPU_LIMITER = anyio.CapacityLimiter(total_tokens=16)

# Dedicated limiter for legacy blocking file operations
IO_LIMITER = anyio.CapacityLimiter(total_tokens=64)

@mcp.tool()
async def calculate_covariance_matrix(matrix_data: List[List[float]]) -> str:
    """Executes CPU-bound linear algebra within an isolated, rate-capped thread pool."""
    result = await anyio.to_thread.run_sync(
        _compute_covariance_sync, 
        matrix_data, 
        limiter=CPU_LIMITER # Isolated limiter prevents thread starvation
    )
    return json.dumps(result)

@mcp.tool()
async def fetch_asset_prices_async(ticker: str) -> str:
    """Uses native non-blocking asyncpg connection pool - uses 0 thread pool tokens."""
    async with db_pool.acquire() as conn:
        records = await conn.fetch("SELECT timestamp, close_price FROM market_prices WHERE ticker = $1", ticker)
        return json.dumps([dict(r) for r in records], default=str)

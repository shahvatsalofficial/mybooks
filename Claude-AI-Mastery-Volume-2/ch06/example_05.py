from contextlib import asynccontextmanager
import asyncpg
import httpx
from starlette.applications import Starlette

@asynccontextmanager
async def lifespan(app: Starlette):
    # --- STARTUP LIFECYCLE ---
    logger.info("Initializing enterprise connection pools...")
    app.state.db_pool = await asyncpg.create_pool(
        dsn=os.getenv("DATABASE_URL"),
        min_size=10,
        max_size=50,
        command_timeout=10.0
    )
    app.state.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(15.0, connect=3.0),
        limits=httpx.Limits(max_keepalive_connections=50, max_connections=200)
    )
    yield
    # --- SHUTDOWN LIFECYCLE ---
    logger.info("Draining connections and terminating server...")
    await app.state.db_pool.close()
    await app.state.http_client.aclose()

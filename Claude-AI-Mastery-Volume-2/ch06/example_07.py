"""
Recipe 06.2: Production Starlette SSE FastMCP Microservice
Author: Vatsal Shah (Opportunity4u Press)
License: Apache-2.0
"""

import os
import logging
from contextlib import asynccontextmanager
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from mcp.server.fastmcp import FastMCP
import uvicorn
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("CloudMCP")

# Initialize FastMCP instance
mcp = FastMCP("cloud-enterprise-mcp")

@mcp.tool()
async def query_cluster_telemetry(cluster_id: str) -> str:
    """Fetches real-time CPU, memory, and pod health metrics for an active Kubernetes cluster."""
    logger.info(f"Querying cluster telemetry for {cluster_id}")
    return json.dumps({
        "cluster_id": cluster_id,
        "status": "HEALTHY",
        "cpu_utilization_pct": 43.8,
        "memory_utilization_pct": 61.2,
        "active_worker_nodes": 18,
        "pending_pods": 0
    })

# --- Security Authentication Middleware ---
class BearerAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, valid_token: str):
        super().__init__(app)
        self.valid_token = valid_token

    async def dispatch(self, request: Request, call_next):
        # Allow open health checks without authentication
        if request.url.path in ("/healthz", "/readyz"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning("Unauthenticated request blocked: missing Bearer token")
            return Response("Unauthorized: Missing Bearer Token", status_code=401)

        token = auth_header.split(" ", 1)[1]
        if token != self.valid_token:
            logger.warning("Unauthorized request blocked: invalid token")
            return Response("Forbidden: Invalid Token", status_code=403)

        return await call_next(request)

# --- Application Lifespan Context Manager ---
@asynccontextmanager
async def lifespan(app: Starlette):
    logger.info("Bootstrap: Initializing shared asynchronous HTTP client...")
    app.state.http_client = httpx.AsyncClient(timeout=10.0)
    yield
    logger.info("Shutdown: Closing HTTP client sessions...")
    await app.state.http_client.aclose()

# Mount health check routes
async def health_check(request: Request):
    return JSONResponse({"status": "OK", "service": "cloud-enterprise-mcp"})

# Instantiate Starlette Application with mounted SSE routes
app = Starlette(
    routes=[
        *mcp.sse_routes(), # Mounts /sse and /messages endpoints
    ],
    middleware=[
        Middleware(BearerAuthMiddleware, valid_token=os.getenv("MCP_AUTH_TOKEN", "prod-secret-99"))
    ],
    lifespan=lifespan
)
app.add_route("/healthz", health_check, methods=["GET"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, access_log=False)

# gateway/main.py
"""Enterprise FastAPI Gateway with Lifespan management and structured telemetry."""

from __future__ import annotations
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
import logging
import time
import uuid

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
import httpx
import uvicorn

# Configure high-performance structured logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("api_gateway")


class ServiceState:
    """Encapsulates shared long-lived network resources across the application lifespan."""
    http_client: httpx.AsyncClient


state = ServiceState()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manages application startup and teardown lifecycles.
    
    Establishes persistent connection pools during boot and gracefully drains
    open sockets during container termination.
    """
    logger.info("Initializing enterprise API Gateway runtime...")
    
    # Initialize connection-pooled non-blocking HTTP client with tuned socket limits
    limits = httpx.Limits(max_keepalive_connections=100, max_connections=500, keepalive_expiry=30.0)
    timeout = httpx.Timeout(connect=2.0, read=5.0, write=5.0, pool=5.0)
    state.http_client = httpx.AsyncClient(limits=limits, timeout=timeout)
    
    logger.info("HTTP persistent connection pools successfully established.")
    yield  # Application serves incoming HTTP traffic
    
    # Teardown phase: gracefully drain and close persistent network pools
    logger.info("Commencing graceful gateway shutdown. Draining connection pools...")
    await state.http_client.aclose()
    logger.info("Gateway shutdown complete. Sockets safely released.")


app = FastAPI(
    title="Enterprise Core Gateway",
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url=None,  # Disable unused Redoc endpoint in production
    lifespan=lifespan,
)


@app.middleware("http")
async def correlation_and_latency_middleware(request: Request, call_next) -> Response:
    """Enforces distributed correlation tracking and records request execution latency."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    
    start_time = time.perf_counter()
    try:
        response: Response = await call_next(request)
    except Exception as exc:
        logger.exception(
            "Unhandled internal exception during request processing. Correlation-ID: %s",
            correlation_id,
        )
        response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred while processing the transaction.",
                "correlation_id": correlation_id,
            },
        )
    
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.2f}"
    
    # Structured access log for centralized log aggregators (ELK / Datadog)
    logger.info(
        "METHOD=%s PATH=%s STATUS=%d DURATION=%.2fms CORRELATION=%s",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
        correlation_id,
    )
    return response


@app.get("/healthz", status_code=status.HTTP_200_OK, tags=["Operations"])
async def liveness_probe() -> dict[str, str]:
    """Lightweight Kubernetes liveness probe validating event loop responsiveness."""
    return {"status": "HEALTHY"}


@app.get("/readyz", status_code=status.HTTP_200_OK, tags=["Operations"])
async def readiness_probe() -> dict[str, str]:
    """Readiness probe verifying connection pool availability."""
    if state.http_client.is_closed:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "UNAVAILABLE", "reason": "HTTP client pool closed"},
        )
    return {"status": "READY"}

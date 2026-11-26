# observability/metrics.py
"""Prometheus RED metrics middleware with high-resolution latency histograms."""

from __future__ import annotations
import time
from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# Bounded, high-resolution exponential latency buckets (1ms to 10 seconds)
LATENCY_BUCKETS = (
    0.001, 0.0025, 0.005, 0.010, 0.025, 0.050, 0.100,
    0.250, 0.500, 1.0, 2.5, 5.0, 10.0,
)

# 1. RATE & ERRORS: Total HTTP request counter
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total incoming HTTP request count partitioned by method, normalized route, and status.",
    ["method", "route", "status_code"],
)

# 2. DURATION: High-resolution request execution latency histogram
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request execution latency distribution in seconds.",
    ["method", "route", "status_code"],
    buckets=LATENCY_BUCKETS,
)


def normalize_route_path(request: Request) -> str:
    """Extracts parameterized route template (e.g., '/orders/{order_id}') to prevent cardinality explosion."""
    for route in request.app.routes:
        match, _ = route.matches(request.scope)
        if match.name == "FULL":
            return route.path
    return request.url.path  # Fallback for unrouted requests


async def prometheus_metrics_middleware(request: Request, call_next) -> Response:
    """Records execution duration and updates Prometheus RED metrics counters."""
    start_time = time.perf_counter()
    status_code = 500

    try:
        response: Response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        elapsed_seconds = time.perf_counter() - start_time
        route = normalize_route_path(request)
        method = request.method

        # Record metrics using STRICT low-cardinality labels
        HTTP_REQUESTS_TOTAL.labels(
            method=method,
            route=route,
            status_code=str(status_code),
        ).inc()

        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=method,
            route=route,
            status_code=str(status_code),
        ).observe(elapsed_seconds)

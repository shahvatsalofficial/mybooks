# tests/test_api_integration.py
"""Asynchronous FastAPI integration tests using in-memory ASGI transport."""

from __future__ import annotations
import pytest
from fastapi import FastAPI, status
import httpx
from unittest.mock import AsyncMock

from gateway.main import app
from database.session import get_db_context


@pytest.fixture
async def async_client(db_session) -> httpx.AsyncClient:
    """Configures non-blocking in-memory HTTP client wired directly to FastAPI ASGI app.
    
    Overrides database dependency with transactional test session.
    """
    # Dependency Override: Wire route handler to the transactional test session
    app.dependency_overrides[get_db_context] = lambda: db_session

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()


async def test_order_submission_end_to_end(async_client: httpx.AsyncClient) -> None:
    """Verifies complete order submission pipeline: validation, persistence, and response headers."""
    payload = {
        "sku": "PRO-DESK-2026",
        "quantity": 2,
        "unit_price": "250.00",
        "currency": "USD",
    }

    response = await async_client.post(
        "/api/v1/orders",
        json=payload,
        headers={"X-API-Key": "test-key-developer"},
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "order_id" in data
    assert data["status"] == "SUBMITTED"
    assert response.headers["X-Process-Time-Ms"] is not None


async def test_order_submission_rejects_negative_quantity(async_client: httpx.AsyncClient) -> None:
    """Verifies that Pydantic V2 schema validation rejects illegal inputs with HTTP 422."""
    invalid_payload = {
        "sku": "PRO-DESK-2026",
        "quantity": -5,  # Illegal negative quantity
        "unit_price": "250.00",
        "currency": "USD",
    }

    response = await async_client.post("/api/v1/orders", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error_details = response.json()
    assert error_details["detail"][0]["loc"] == ["body", "quantity"]

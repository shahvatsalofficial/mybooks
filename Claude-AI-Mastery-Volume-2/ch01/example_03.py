"""
Recipe 01.3: Multi-Tenant Claude API Gateway with Model Routing & Prometheus Metrics
Author: Vatsal Shah (Vatsal Shah)
License: Apache-2.0
"""

import time
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, Header
from pydantic import BaseModel, Field
import httpx
from prometheus_client import Counter, Histogram, make_asgi_app

logger = logging.getLogger("GatewayRouter")

# --- Prometheus Observability Instrumentation ---
REQUEST_COUNTER = Counter(
    "claude_gateway_requests_total",
    "Total requests processed by gateway",
    ["tenant_id", "model_tier", "status"]
)
TOKEN_CONSUMPTION = Counter(
    "claude_gateway_tokens_total",
    "Tokens processed across model tiers",
    ["tenant_id", "model_tier", "token_type"]
)
INFERENCE_LATENCY = Histogram(
    "claude_gateway_inference_latency_seconds",
    "End-to-end inference latency in seconds",
    ["model_tier"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0]
)

app = FastAPI(title="Enterprise Claude Gateway", version="2.0.0")
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# --- Authorized Tenants & Configuration ---
TENANT_CONFIG = {
    "tenant-fintech-core": {"tpm_limit": 400_000, "allowed_models": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"]},
    "tenant-marketing-ops": {"tpm_limit": 100_000, "allowed_models": ["claude-3-5-haiku-20241022"]}
}

class IngressPayload(BaseModel):
    task_complexity: str = Field(..., pattern="^(low|medium|high|critical)$")
    messages: list
    system_prompt: Optional[str] = None
    max_tokens: int = 2048

def resolve_optimal_model(complexity: str) -> str:
    """Dynamic routing algorithm based on SLA and cost optimization."""
    if complexity in ("low", "medium"):
        return "claude-3-5-haiku-20241022"
    elif complexity == "high":
        return "claude-3-5-sonnet-20241022"
    elif complexity == "critical":
        # Extended reasoning tier
        return "claude-3-7-sonnet-20250219"
    return "claude-3-5-sonnet-20241022"

@app.post("/v1/enterprise/chat")
async def handle_tenant_chat(
    payload: IngressPayload,
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
    x_auth_token: str = Header(..., alias="Authorization")
):
    if x_tenant_id not in TENANT_CONFIG:
        raise HTTPException(status_code=403, detail="Unauthorized tenant identifier.")

    target_model = resolve_optimal_model(payload.task_complexity)
    
    # Enforce tenant model permissions
    allowed = TENANT_CONFIG[x_tenant_id]["allowed_models"]
    if target_model not in allowed:
        # Fallback to highest permitted tier
        target_model = allowed[0]

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    body = {
        "model": target_model,
        "messages": payload.messages,
        "max_tokens": payload.max_tokens,
        "temperature": 0.0
    }
    if payload.system_prompt:
        body["system"] = payload.system_prompt

    start_time = time.perf_counter()
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=body)
            duration = time.perf_counter() - start_time
            INFERENCE_LATENCY.labels(model_tier=target_model).observe(duration)

            if resp.status_code != 200:
                REQUEST_COUNTER.labels(tenant_id=x_tenant_id, model_tier=target_model, status="error").inc()
                raise HTTPException(status_code=resp.status_code, detail=resp.text)

            data = resp.json()
            usage = data.get("usage", {})
            
            # Record Token Observability
            TOKEN_CONSUMPTION.labels(tenant_id=x_tenant_id, model_tier=target_model, token_type="input").inc(usage.get("input_tokens", 0))
            TOKEN_CONSUMPTION.labels(tenant_id=x_tenant_id, model_tier=target_model, token_type="output").inc(usage.get("output_tokens", 0))
            TOKEN_CONSUMPTION.labels(tenant_id=x_tenant_id, model_tier=target_model, token_type="cache_read").inc(usage.get("cache_read_input_tokens", 0))
            
            REQUEST_COUNTER.labels(tenant_id=x_tenant_id, model_tier=target_model, status="success").inc()
            return data

        except httpx.RequestError as exc:
            REQUEST_COUNTER.labels(tenant_id=x_tenant_id, model_tier=target_model, status="network_failure").inc()
            raise HTTPException(status_code=504, detail=f"Upstream Anthropic network error: {str(exc)}")

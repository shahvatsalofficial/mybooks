"""
Production Multi-Tenant OpenAI Proxy Gatekeeper
Enforces internal client quotas via Redis sliding-window before forwarding upstream.
"""
from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.responses import StreamingResponse
import redis.asyncio as aioredis
import httpx
import os
import time
import json
import logging

app = FastAPI(title="Enterprise OpenAI Multi-Tenant Proxy")
redis_client = aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
UPSTREAM_OPENAI_URL = "https://api.openai.com/v1/chat/completions"
MASTER_OPENAI_KEY = os.getenv("OPENAI_MASTER_API_KEY")

logger = logging.getLogger("ProxyGatekeeper")

# Tenant Quota Allocations: (Allowed RPM, Allowed TPM)
TENANT_QUOTAS = {
    "tenant_analytics_prod": {"rpm": 2000, "tpm": 2500000},
    "tenant_customer_bot":   {"rpm": 5000, "tpm": 5000000},
    "tenant_dev_sandbox":    {"rpm": 100,  "tpm": 100000},
}

LUA_SLIDING_WINDOW_RATE_LIMITER = """
local tenant_key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local max_limit = tonumber(ARGV[3])
local cost = tonumber(ARGV[4])

-- Clean entries older than sliding window
redis.call('ZREMRANGEBYSCORE', tenant_key, '-inf', now - window)

-- Sum current consumption within window
local entries = redis.call('ZRANGE', tenant_key, 0, -1, 'WITHSCORES')
local current_usage = 0
for i = 1, #entries, 2 do
    local member = entries[i]
    local member_cost = tonumber(string.match(member, ":(%d+)$"))
    if member_cost then
        current_usage = current_usage + member_cost
    end
end

if current_usage + cost <= max_limit then
    local entry_id = tostring(now) .. ":" .. tostring(cost) .. ":" .. tostring(math.random(100000, 999999))
    redis.call('ZADD', tenant_key, now, entry_id)
    redis.call('EXPIRE', tenant_key, math.ceil(window))
    return 1
else
    return 0
end
"""

async def verify_tenant_quota(
    x_tenant_id: str = Header(...),
    x_tenant_secret: str = Header(...)
) -> str:
    if x_tenant_id not in TENANT_QUOTAS:
        raise HTTPException(status_code=403, detail="Unregistered enterprise tenant identifier.")
    return x_tenant_id

@app.post("/v1/chat/completions")
async def proxy_chat_completions(
    request: Request,
    tenant_id: str = Depends(verify_tenant_quota)
):
    body_bytes = await request.body()
    try:
        payload = json.loads(body_bytes)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload structure.")

    model = payload.get("model", "gpt-4o")
    max_tokens = payload.get("max_tokens", 2048)
    # Estimate token load: 1 character ~ 0.25 tokens heuristic + requested max
    estimated_prompt_tokens = int(len(str(payload.get("messages", ""))) * 0.28)
    estimated_total_cost = estimated_prompt_tokens + max_tokens

    # Enforce Redis Sliding-Window Rate Limit
    now = time.time()
    tpm_key = f"rate_limit:tpm:{tenant_id}"
    allowed = await redis_client.eval(
        LUA_SLIDING_WINDOW_RATE_LIMITER,
        1,
        tpm_key,
        now,
        60.0,
        TENANT_QUOTAS[tenant_id]["tpm"],
        estimated_total_cost
    )

    if not allowed:
        logger.warning(f"Tenant {tenant_id} throttled: Breached internal TPM quota.")
        raise HTTPException(
            status_code=429,
            detail=f"Tenant {tenant_id} exceeded allocated internal Tokens-Per-Minute quota."
        )

    # Forward to OpenAI Gateway
    client = httpx.AsyncClient(timeout=60.0)
    headers = {
        "Authorization": f"Bearer {MASTER_OPENAI_KEY}",
        "Content-Type": "application/json"
    }

    if payload.get("stream", False):
        req = client.build_request("POST", UPSTREAM_OPENAI_URL, json=payload, headers=headers)
        r = await client.send(req, stream=True)
        return StreamingResponse(
            r.aiter_bytes(),
            status_code=r.status_code,
            media_type="text/event-stream",
            background=client.aclose
        )
    else:
        resp = await client.post(UPSTREAM_OPENAI_URL, json=payload, headers=headers)
        await client.aclose()
        return resp.json()

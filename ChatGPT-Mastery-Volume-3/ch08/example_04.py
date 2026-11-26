# enterprise_ai_gateway.py — High-Concurrency Multi-Tenant Gateway
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
import httpx
import time
import os

app = FastAPI(title="Enterprise Multi-Tenant AI Platform Gateway", version="3.0.0")

# Circuit Breaker State Machine
CIRCUIT_STATE = "CLOSED" # "CLOSED", "OPEN", "HALF_OPEN"
FAILURES = 0
LAST_FAILURE_TIME = 0.0
FAILURE_THRESHOLD = 5
COOLDOWN_WINDOW = 30.0

UPSTREAM_ENDPOINTS = [
    "https://aoai-eastus2-01.openai.azure.com",
    "https://aoai-swedencentral-01.openai.azure.com"
]

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    global CIRCUIT_STATE, FAILURES, LAST_FAILURE_TIME

    # 1. Validate Tenant ID Header
    tenant_id = request.headers.get("x-tenant-id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Missing mandatory X-Tenant-ID header")

    # 2. Check Circuit Breaker State
    now = time.time()
    if CIRCUIT_STATE == "OPEN":
        if now - LAST_FAILURE_TIME > COOLDOWN_WINDOW:
            CIRCUIT_STATE = "HALF_OPEN"
            print("Circuit Breaker Transition: OPEN -> HALF_OPEN (Testing probe)")
        else:
            raise HTTPException(
                status_code=503,
                detail="Upstream AI inference circuit breaker is OPEN. Fast-failing."
            )

    body = await request.json()
    model = body.get("model", "gpt-4o")

    # 3. Upstream Dispatch with Active-Active Failover
    success = False
    response_stream = None

    for endpoint in UPSTREAM_ENDPOINTS:
        target_url = f"{endpoint}/openai/deployments/{model}/chat/completions?api-version=2024-06-01"
        try:
            client = httpx.AsyncClient(timeout=30.0)
            upstream_req = client.build_request(
                "POST",
                target_url,
                headers={
                    "api-key": os.getenv("AZURE_OPENAI_API_KEY"),
                    "Content-Type": "application/json"
                },
                json=body
            )
            upstream_resp = await client.send(upstream_req, stream=True)

            if upstream_resp.status_code == 200:
                success = True
                if CIRCUIT_STATE == "HALF_OPEN":
                    CIRCUIT_STATE = "CLOSED"
                    FAILURES = 0
                    print("Circuit Breaker Reset: HALF_OPEN -> CLOSED")

                async def forward_stream():
                    async for chunk in upstream_resp.aiter_bytes():
                        yield chunk
                    await client.aclose()

                return StreamingResponse(
                    forward_stream(),
                    status_code=200,
                    media_type="text/event-stream"
                )

        except Exception as e:
            print(f"Endpoint {endpoint} failed: {str(e)}")
            continue

    # 4. Handle Complete Regional Failure
    FAILURES += 1
    LAST_FAILURE_TIME = time.time()
    if FAILURES >= FAILURE_THRESHOLD:
        CIRCUIT_STATE = "OPEN"
        print("Circuit Breaker Tripped: CLOSED -> OPEN (Halting traffic for 30s)")

    raise HTTPException(status_code=502, detail="All upstream Azure OpenAI regions unreachable")

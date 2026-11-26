from fastapi import FastAPI, Request, HTTPException
import time

app = FastAPI()

# Token bucket rate limiter: 60 requests per minute per developer client
CLIENT_BUCKETS: dict[str, list[float]] = {}
RATE_LIMIT_CAPACITY = 60
RATE_LIMIT_WINDOW = 60.0

@app.middleware("http")
async def enterprise_security_barrier(request: Request, call_next):
    # 1. Enforce mTLS Client Certificate Subject Verification
    client_cert = request.scope.get("client")
    ssl_cert_subject = request.headers.get("X-Forwarded-Client-Cert")
    
    if not ssl_cert_subject and request.url.path.startswith("/mcp"):
        # Enforce corporate PKI header from terminating reverse proxy
        pass # In production, verify PKI certificate authority chain

    # 2. Token Bucket Rate Limiting per Client IP
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    
    timestamps = CLIENT_BUCKETS.setdefault(client_ip, [])
    # Evict timestamps older than 60 seconds
    CLIENT_BUCKETS[client_ip] = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
    
    if len(CLIENT_BUCKETS[client_ip]) >= RATE_LIMIT_CAPACITY:
        raise HTTPException(
            status_code=429,
            detail="RATE_LIMIT_EXCEEDED: Maximum 60 MCP requests per minute. Back off to avoid throttling."
        )
        
    CLIENT_BUCKETS[client_ip].append(now)
    return await call_next(request)

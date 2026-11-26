"""
Enterprise ASGI Interceptor Pipeline for MCP Transports
Features: Token Bucket Rate Limiting, Scope Mapping & Structured Audit Trail
Author: Vatsal Shah | Opportunity4u Press
"""

import time
import json
import logging
import asyncio
from typing import Callable, Dict, Any, Awaitable
from contextvars import ContextVar

# Thread-safe request context propagation
CURRENT_TENANT_ID: ContextVar[str] = ContextVar("CURRENT_TENANT_ID", default="anonymous")
CURRENT_CALLER_ID: ContextVar[str] = ContextVar("CURRENT_CALLER_ID", default="unauthenticated")

logger = logging.getLogger("mcp.interceptor")

class TokenBucketRateLimiter:
    """Thread-safe in-memory token bucket rate limiter per caller."""

    def __init__(self, capacity: int = 60, refill_rate_per_sec: float = 1.0):
        self.capacity = float(capacity)
        self.refill_rate = refill_rate_per_sec
        self.buckets: Dict[str, Dict[str, float]] = {}
        self._lock = asyncio.Lock()

    async def acquire(self, caller_id: str, cost: float = 1.0) -> bool:
        async with self._lock:
            now = time.monotonic()
            if caller_id not in self.buckets:
                self.buckets[caller_id] = {"tokens": self.capacity, "last_updated": now}

            state = self.buckets[caller_id]
            elapsed = now - state["last_updated"]
            state["tokens"] = min(self.capacity, state["tokens"] + elapsed * self.refill_rate)
            state["last_updated"] = now

            if state["tokens"] >= cost:
                state["tokens"] -= cost
                return True
            return False


class McpSecurityInterceptorPipeline:
    """Layered interceptor onion processing raw JSON-RPC 2.0 frames."""

    def __init__(self, rate_limiter: TokenBucketRateLimiter):
        self.rate_limiter = rate_limiter

    async def process_frame(
        self,
        raw_message: str,
        auth_context: Dict[str, Any],
        handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()
        caller_id = auth_context.get("sub", "anonymous")
        tenant_id = auth_context.get("tenant_id", "default_tenant")
        granted_scopes = set(auth_context.get("scopes", []))

        # 1. Bind asynchronous context stores
        t_token = CURRENT_TENANT_ID.set(tenant_id)
        c_token = CURRENT_CALLER_ID.set(caller_id)

        try:
            # 2. Parse JSON-RPC 2.0 structure
            try:
                rpc_req = json.loads(raw_message)
            except json.JSONDecodeError:
                return {
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": "Parse error: Invalid JSON payload"},
                    "id": None
                }

            msg_id = rpc_req.get("id")
            method = rpc_req.get("method")
            params = rpc_req.get("params", {})

            # 3. Enforce rate limiting
            allowed = await self.rate_limiter.acquire(caller_id)
            if not allowed:
                logger.warning(f"Rate limit exceeded for caller: {caller_id}")
                return {
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": "Too Many Requests: Rate limit quota exhausted"},
                    "id": msg_id
                }

            # 4. Enforce Scope Guard on tool invocation
            if method == "tools/call":
                tool_name = params.get("name")
                required_scope = f"mcp:tools:{tool_name}"

                if "mcp:admin" not in granted_scopes and required_scope not in granted_scopes:
                    logger.error(
                        f"Authorization Denied: Caller '{caller_id}' lacks required scope '{required_scope}' "
                        f"for tool '{tool_name}'"
                    )
                    return {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32003,
                            "message": f"Forbidden: Caller lacks scope '{required_scope}'"
                        },
                        "id": msg_id
                    }

            # 5. Execute downstream tool logic
            response = await handler(rpc_req)

            # 6. Audit Logging
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.info(
                f"[AUDIT] caller={caller_id} tenant={tenant_id} method={method} "
                f"duration_ms={duration_ms:.2f} status=SUCCESS"
            )
            return response

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.exception(f"[AUDIT FAIL] caller={caller_id} error={str(exc)} duration_ms={duration_ms:.2f}")
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": f"Internal server error: {str(exc)}"},
                "id": rpc_req.get("id") if "rpc_req" in locals() else None
            }

        finally:
            CURRENT_TENANT_ID.reset(t_token)
            CURRENT_CALLER_ID.reset(c_token)

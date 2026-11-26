import time
from collections import defaultdict

class TokenBucketLimiter:
    def __init__(self, capacity: int = 10, refill_rate_per_sec: float = 10.0 / 60.0):
        self.capacity = capacity
        self.refill_rate = refill_rate_per_sec
        self.tokens = defaultdict(lambda: capacity)
        self.last_update = defaultdict(time.monotonic)

    def allow_request(self, client_id: str = "default") -> bool:
        now = time.monotonic()
        elapsed = now - self.last_update[client_id]
        self.last_update[client_id] = now
        self.tokens[client_id] = min(self.capacity, self.tokens[client_id] + elapsed * self.refill_rate)

        if self.tokens[client_id] >= 1.0:
            self.tokens[client_id] -= 1.0
            return True
        return False

# In lifespan context manager:
@asynccontextmanager
async def rate_limited_lifespan(server: FastMCP):
    limiter = TokenBucketLimiter(capacity=10)
    yield {"limiter": limiter}

# Inside tool handler:
@mcp.tool()
async def rate_guarded_tool(ctx: Context) -> str:
    limiter: TokenBucketLimiter = ctx.request_context.lifespan_context["limiter"]
    if not limiter.allow_request():
        raise PermissionError("Rate limit exceeded: Maximum 10 requests per minute.")
    return "Action executed within rate limit."

# Chaos injection middleware for staging resilience verification
import asyncio
import random

async def chaos_latency_injection_middleware(request, call_next):
    # Simulate 15% random latency degradation (2.5s) on staging
    if random.random() < 0.15:
        await asyncio.sleep(2.5)
    return await call_next(request)

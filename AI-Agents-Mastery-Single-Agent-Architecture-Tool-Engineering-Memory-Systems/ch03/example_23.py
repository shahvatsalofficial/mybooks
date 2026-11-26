import asyncio
import time

def rate_limited_tool(max_calls_per_second: int = 10):
    interval = 1.0 / max_calls_per_second
    lock = asyncio.Lock()
    last_called = [0.0]

    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            async with lock:
                elapsed = time.time() - last_called[0]
                if elapsed < interval:
                    await asyncio.sleep(interval - elapsed)
                last_called[0] = time.time()
            return await func(*args, **kwargs)
        return wrapper
    return decorator

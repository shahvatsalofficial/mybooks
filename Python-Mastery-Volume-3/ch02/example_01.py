# Enabling uvloop in production ASGI runners
import asyncio
import uvloop

# Install uvloop as the global event loop policy
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

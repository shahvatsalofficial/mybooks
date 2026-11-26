# Enable asyncio slow-callback detector in development
import asyncio
import logging

loop = asyncio.get_event_loop()
loop.set_debug(True)
# Emit a CRITICAL log warning whenever any coroutine blocks the loop for > 50ms
loop.slow_callback_duration = 0.050

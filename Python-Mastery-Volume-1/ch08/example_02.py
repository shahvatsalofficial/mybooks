# FATAL ARCHITECTURAL ANTI-PATTERN: NEVER DO THIS IN PRODUCTION
async def worker_loop(queue: asyncio.Queue) -> None:
    while True:
        try:
            item = await queue.get()
            await process_item(item)
        except BaseException as err: # FATAL: Traps CancelledError, SIGINT, SIGTERM
            logger.error(f"Worker caught error: {err}")
            await asyncio.sleep(1) # Coroutine refuses to cancel, deadlocking shutdown!

# THE SEV-1 DEFECT IN ORDER ROUTER (order_router.py:L142)
async def dispatch_order_worker(order_queue: asyncio.Queue) -> None:
    while True:
        try:
            order = await order_queue.get()
            await transmit_to_exchange(order)
            order_queue.task_done()
        except BaseException as err: # CATASTROPHIC ANTI-PATTERN
            logger.error(f"Order dispatch error trapped: {err}")
            await asyncio.sleep(0.5) # Re-attempts forever

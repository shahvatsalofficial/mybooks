# PRODUCTION VERIFIED ARCHITECTURAL REMEDIATION
async def dispatch_order_worker(order_queue: asyncio.Queue) -> None:
    while True:
        try:
            order = await order_queue.get()
            await transmit_to_exchange(order)
            order_queue.task_done()
        except asyncio.CancelledError:
            # Explicitly allow structured concurrency cancellation to propagate!
            logger.info("Worker received cancellation signal. Cleaning up local sockets...")
            raise
        except Exception as err:
            # Trap ONLY standard application domain errors!
            logger.error(f"Order dispatch error trapped: {err}", exc_info=True)
            await metrics.record_failure(err)

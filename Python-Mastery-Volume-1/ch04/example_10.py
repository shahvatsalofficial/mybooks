# DEFECTIVE PRODUCTION CODE (Pre-Incident)
async def process_checkout(user_id: str, order_data: dict) -> None:
    # Anti-pattern: Detached fire-and-forget task without structured scope
    asyncio.create_task(_settle_payment_and_release_inventory(user_id, order_data))


async def _settle_payment_and_release_inventory(user_id: str, order_data: dict) -> None:
    conn = await db_pool.acquire()
    try:
        # Anti-pattern: Catching generic Exception ignores CancelledError!
        # In Python, CancelledError inherits from BaseException in Python 3.8+!
        await conn.execute("BEGIN;")
        await call_payment_gateway(order_data)
        await conn.execute("UPDATE inventory SET ...;")
        await conn.execute("COMMIT;")
    except Exception as e:
        logger.error(f"Transaction failed: {e}")
        await conn.execute("ROLLBACK;")
        await db_pool.release(conn)
    # FATAL DEFECT: If CancelledError is thrown, the except block is SKIPPED,
    # and db_pool.release(conn) is NEVER CALLED!

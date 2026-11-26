# PRODUCTION REMEDIATION (Post-Incident)
async def process_checkout_hardened(user_id: str, order_data: dict) -> None:
    # Enforce structured concurrency boundary
    async with asyncio.TaskGroup() as tg:
        tg.create_task(_settle_payment_hardened(user_id, order_data))


async def _settle_payment_hardened(user_id: str, order_data: dict) -> None:
    # Guaranteed deterministic cleanup via async context manager
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            # conn.transaction() automatically issues ROLLBACK on CancelledError
            await call_payment_gateway(order_data)
            await conn.execute("UPDATE inventory SET ...;")
            # Automatic COMMIT upon successful block exit

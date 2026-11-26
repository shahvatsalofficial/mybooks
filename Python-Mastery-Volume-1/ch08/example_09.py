async with acquire_db() as db, acquire_redis() as redis:
    await execute_sync(db, redis)

class AsyncDatabaseTransaction:
    def __init__(self, pool: ConnectionPool) -> None:
        self.pool = pool
        self.conn: Connection | None = None

    async def __aenter__(self) -> Connection:
        # Non-blocking acquisition of connection from pool
        self.conn = await self.pool.acquire()
        await self.conn.execute("BEGIN TRANSACTION;")
        return self.conn

    async def __aexit__(self, exc_type: type | None, exc_val: Exception | None, tb: object) -> None:
        if self.conn is None:
            return
        try:
            if exc_type is not None:
                # Caught exception or CancelledError: Roll back!
                await self.conn.execute("ROLLBACK;")
            else:
                await self.conn.execute("COMMIT;")
        finally:
            # Deterministic return to pool under all circumstances
            await self.pool.release(self.conn)

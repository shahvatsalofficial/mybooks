import types
from typing import Self

class EnterprisePostgresTransaction:
    def __init__(self, pool: ConnectionPool, isolation_level: str = "REPEATABLE READ") -> None:
        self.pool = pool
        self.isolation_level = isolation_level
        self.conn: Connection | None = None

    async def __aenter__(self) -> Connection:
        self.conn = await self.pool.acquire()
        await self.conn.execute(f"BEGIN TRANSACTION ISOLATION LEVEL {self.isolation_level}")
        return self.conn

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None
    ) -> bool:
        try:
            if exc_type is not None:
                # An exception occurred inside the with block: Roll back
                if self.conn:
                    await self.conn.execute("ROLLBACK")
                logger.warning(f"Transaction aborted due to {exc_type.__name__}: {exc_val}. Changes rolled back.")
                # Return False (or None) to allow the exception to propagate to caller!
                return False
            else:
                # Execution succeeded cleanly: Commit
                if self.conn:
                    await self.conn.execute("COMMIT")
                return True
        finally:
            if self.conn:
                await self.pool.release(self.conn)
                self.conn = None

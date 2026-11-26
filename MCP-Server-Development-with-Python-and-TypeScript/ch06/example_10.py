"""
recipe_6_3_async_sqlite_lifespan.py
Production SQLite connection pool management with FastMCP lifespan context.
"""

import sys
import aiosqlite
from contextlib import asynccontextmanager
from typing import AsyncIterator
from mcp.server.fastmcp import FastMCP, Context
from pydantic import BaseModel, Field

DATABASE_PATH = "enterprise_audit.db"


@asynccontextmanager
async def database_lifespan(server: FastMCP) -> AsyncIterator[dict]:
    """Manages the lifecycle of the SQLite database connection."""
    sys.stderr.write("[Lifespan] Initializing database schema...\n")
    db = await aiosqlite.connect(DATABASE_PATH)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor TEXT NOT NULL,
            action TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await db.commit()

    try:
        # Yield connection to active server handlers
        yield {"db": db}
    finally:
        # GRACEFUL TEARDOWN
        sys.stderr.write("[Lifespan] Closing database connection...\n")
        await db.close()
        sys.stderr.write("[Lifespan] Database closed cleanly.\n")


mcp = FastMCP("AuditLoggingServer", lifespan=database_lifespan)


class AuditEntry(BaseModel):
    actor: str = Field(..., description="Username or service account performing the action.")
    action: str = Field(..., description="Action identifier (e.g., 'auth.login', 'file.delete').")


@mcp.tool()
async def record_audit_event(entry: AuditEntry, ctx: Context) -> str:
    """Inserts a structured audit event into the enterprise SQLite database."""
    # Retrieve pooled connection from lifespan context
    db: aiosqlite.Connection = ctx.request_context.lifespan_context["db"]

    async with db.execute(
        "INSERT INTO audit_logs (actor, action) VALUES (?, ?)",
        (entry.actor, entry.action)
    ) as cursor:
        await db.commit()
        record_id = cursor.lastrowid

    return f"Audit event #{record_id} successfully recorded for actor '{entry.actor}'."


if __name__ == "__main__":
    mcp.run(transport="stdio")

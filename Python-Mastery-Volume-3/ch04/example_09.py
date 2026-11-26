# database/session.py
"""Enterprise SQLAlchemy 2.0 asynchronous database session factory."""

from __future__ import annotations
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool

logger = logging.getLogger("database_engine")

DATABASE_URL = "postgresql+asyncpg://postgres:secret@localhost:5432/enterprise_db"


def create_enterprise_engine(database_url: str) -> AsyncEngine:
    """Configures high-throughput AsyncEngine with optimized pool parameters."""
    return create_async_engine(
        database_url,
        poolclass=AsyncAdaptedQueuePool,
        pool_size=10,             # Persistent pool size per worker
        max_overflow=5,           # Burst capacity above pool_size
        pool_timeout=10.0,        # Fail fast if pool exhausted (seconds)
        pool_recycle=1800,        # Recycle connections every 30 mins to avoid stale TCP sockets
        pool_pre_ping=True,       # Validate socket health with 'SELECT 1' before checkout
        echo=False,               # Disable raw SQL stdout in production
        connect_args={
            "server_settings": {
                "application_name": "enterprise_api_gateway",
                "statement_timeout": "15000",  # Kill runaway queries after 15 seconds
                "idle_in_transaction_session_timeout": "30000", # Abort uncommitted idle transactions
            }
        },
    )


engine = create_enterprise_engine(DATABASE_URL)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # CRITICAL: Prevent greenlet errors post-commit
    autoflush=False,         # Explicit flush control
)


@asynccontextmanager
async def get_db_context() -> AsyncIterator[AsyncSession]:
    """Provides a transactional database session context manager with automatic rollback."""
    session: AsyncSession = async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception as exc:
        logger.warning("Database transaction aborted. Rolling back: %s", exc)
        await session.rollback()
        raise
    finally:
        await session.close()

# tests/conftest.py
"""Enterprise test harness managing Docker Testcontainers and database transaction boundaries."""

from __future__ import annotations
from collections.abc import AsyncIterator
import os
import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
import redis.asyncio as aioredis

from database.session import Base


# ═══════════════════════════════════════════════════════════════════════
# Session-Scoped Containers: Booted ONCE per test suite invocation
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def postgres_container():
    """Boots ephemeral PostgreSQL 16 container on a random host port."""
    with PostgresContainer("postgres:16-alpine") as container:
        # Export dynamic database URL (e.g., localhost:49152)
        yield container


@pytest.fixture(scope="session")
def redis_container():
    """Boots ephemeral Redis 7 container on a random host port."""
    with RedisContainer("redis:7-alpine") as container:
        yield container


@pytest.fixture(scope="session")
async def db_engine(postgres_container) -> AsyncIterator[AsyncEngine]:
    """Creates SQLAlchemy AsyncEngine connected to the ephemeral PostgreSQL container."""
    # Convert sync driver URL to asyncpg driver URL
    sync_url = postgres_container.get_connection_url()
    async_url = sync_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(async_url, pool_pre_ping=True, echo=False)

    # Apply database schema metadata across ephemeral container
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


# ═══════════════════════════════════════════════════════════════════════
# Function-Scoped Sessions: Total Transactional Isolation per Test
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="function")
async def db_session(db_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Provides an isolated AsyncSession wrapped in an outer transaction that rolls back.
    
    Guarantees that database modifications made during a test are NEVER committed
    to the container, leaving the database completely clean for subsequent tests.
    """
    connection = await db_engine.connect()
    transaction = await connection.begin()

    session_factory = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    session = session_factory()

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()


@pytest.fixture(scope="function")
async def redis_client(redis_container) -> AsyncIterator[aioredis.Redis]:
    """Provides a fresh Redis client flushed cleanly before each test function."""
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(redis_container.port)
    client = aioredis.from_url(f"redis://{host}:{port}/0")

    await client.flushdb()  # Flush keyspace before test execution
    yield client
    await client.aclose()

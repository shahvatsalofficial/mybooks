# Enterprise Scoped Dependency Pattern
async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Provides a transactional database session scoped to a single HTTP request."""
    session = async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

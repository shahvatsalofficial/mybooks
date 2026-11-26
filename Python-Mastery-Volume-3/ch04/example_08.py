# Acquiring a PostgreSQL transactional advisory lock in SQLAlchemy 2.0
async def acquire_reconciliation_lock(session: AsyncSession, account_id_int: int) -> bool:
    """Attempts to acquire a transactional advisory lock without waiting."""
    stmt = select(func.pg_try_advisory_xact_lock(account_id_int))
    result = await session.execute(stmt)
    acquired = result.scalar_one()
    return bool(acquired)

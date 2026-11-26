import pytest
from collections.abc import AsyncIterator

@pytest.fixture(scope="function")
async def managed_database_transaction(db_session) -> AsyncIterator[None]:
    # SETUP PHASE: Executed before the test runs
    transaction = await db_session.begin_nested() # Create SAVEPOINT
    try:
        yield  # Control hands over to the test function
    finally:
        # TEARDOWN PHASE: Guaranteed to execute even if test raises an exception
        await transaction.rollback()

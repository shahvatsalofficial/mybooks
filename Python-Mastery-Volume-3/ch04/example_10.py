# database/account_repository.py
"""Pessimistic locking repository for high-concurrency balance modifications."""

from __future__ import annotations
import asyncio
from decimal import Decimal
import logging
import random
import uuid

import asyncpg.exceptions
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import AccountModel

logger = logging.getLogger("account_repo")


class LockAcquisitionError(Exception):
    """Raised when a pessimistic lock cannot be acquired within retry limits."""
    pass


class InsufficientFundsError(Exception):
    """Raised when account balance is lower than requested withdrawal."""
    pass


class AccountRepository:
    """Encapsulates pessimistic locking and atomic balance debit operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def debit_account_with_retry(
        self,
        account_id: uuid.UUID,
        amount: Decimal,
        max_attempts: int = 5,
    ) -> AccountModel:
        """Atomically debits an account using FOR UPDATE NOWAIT and exponential jittered retries."""
        for attempt in range(1, max_attempts + 1):
            try:
                # Query account with fail-fast pessimistic row lock
                stmt = (
                    select(AccountModel)
                    .where(AccountModel.id == account_id)
                    .with_for_update(nowait=True)
                )
                result = await self.session.execute(stmt)
                account = result.scalar_one_or_none()

                if account is None:
                    raise ValueError(f"Account with ID {account_id} not found.")

                if account.balance < amount:
                    raise InsufficientFundsError(
                        f"Insufficient funds: Balance ${account.balance:,.2f} < Debit ${amount:,.2f}"
                    )

                # Mutate balance atomically within lock
                account.balance -= amount
                await self.session.flush()
                logger.info("Successfully debited $%.2f from account %s", amount, account_id)
                return account

            except DBAPIError as err:
                # Check for PostgreSQL 55P03 lock_not_available error
                is_lock_error = isinstance(err.orig, asyncpg.exceptions.LockNotAvailableError)
                if is_lock_error and attempt < max_attempts:
                    # Calculate randomized jittered exponential backoff: base * 2^attempt + jitter
                    delay = (0.05 * (2 ** attempt)) + random.uniform(0.01, 0.05)
                    logger.warning(
                        "Account %s locked by concurrent transaction. Retrying (Attempt %d/%d) in %.3fs...",
                        account_id,
                        attempt,
                        max_attempts,
                        delay,
                    )
                    await self.session.rollback()
                    await asyncio.sleep(delay)
                else:
                    logger.error("Failed to acquire row lock on account %s after %d attempts", account_id, attempt)
                    await self.session.rollback()
                    raise LockAcquisitionError(f"Account {account_id} is heavily contended.") from err

        raise LockAcquisitionError("Maximum retry ceiling reached without lock acquisition.")

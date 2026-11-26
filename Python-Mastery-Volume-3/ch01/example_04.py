# application/ports.py
"""Abstract Port specifications for persistence and Unit of Work coordination."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Self
import uuid

from domain.model import OrderAggregate, OrderId


class AbstractOrderRepository(ABC):
    """Abstract Port representing an in-memory collection of Order aggregates."""

    @abstractmethod
    async def get_by_id(self, order_id: OrderId) -> OrderAggregate | None:
        """Retrieve an aggregate by unique ID or return None."""

    @abstractmethod
    async def add(self, order: OrderAggregate) -> None:
        """Stage an aggregate for persistence."""


class AbstractUnitOfWork(ABC):
    """Abstract Context Manager providing atomic transactional execution boundaries."""

    orders: AbstractOrderRepository

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

    @abstractmethod
    async def commit(self) -> None:
        """Atomically commit all staged aggregate mutations to durable storage."""

    @abstractmethod
    async def rollback(self) -> None:
        """Discard uncommitted modifications and release database resources."""

# infrastructure/uow.py
"""Concrete In-Memory Test Double implementation of Unit of Work for sub-millisecond testing."""

from __future__ import annotations
from domain.model import OrderAggregate, OrderId
from application.ports import AbstractOrderRepository, AbstractUnitOfWork


class InMemoryOrderRepository(AbstractOrderRepository):
    """Thread-safe in-memory collection double for unit tests."""

    def __init__(self) -> None:
        self._storage: dict[OrderId, OrderAggregate] = {}

    async def get_by_id(self, order_id: OrderId) -> OrderAggregate | None:
        return self._storage.get(order_id)

    async def add(self, order: OrderAggregate) -> None:
        self._storage[order.id] = order


class InMemoryUnitOfWork(AbstractUnitOfWork):
    """In-memory Unit of Work implementing atomic commit and rollback emulation."""

    def __init__(self) -> None:
        self.orders = InMemoryOrderRepository()
        self.committed = False
        self.rolled_back = False

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True

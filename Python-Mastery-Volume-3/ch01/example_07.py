# application/use_cases.py
"""Application layer use cases orchestrating aggregates, persistence, and event dispatching."""

from __future__ import annotations
from decimal import Decimal
import uuid

from domain.model import Currency, Money, OrderAggregate, OrderId, SkuId
from application.ports import AbstractUnitOfWork
from infrastructure.event_bus import AsyncEventDispatcher


class SubmitOrderUseCase:
    """Orchestrates order aggregate retrieval, invariant execution, and persistence."""

    def __init__(self, uow: AbstractUnitOfWork, dispatcher: AsyncEventDispatcher) -> None:
        self.uow = uow
        self.dispatcher = dispatcher

    async def execute(
        self,
        order_id: OrderId,
        customer_id: uuid.UUID,
        sku: str,
        price_amount: str,
        quantity: int,
    ) -> OrderId:
        async with self.uow:
            order = await self.uow.orders.get_by_id(order_id)
            if order is None:
                order = OrderAggregate(
                    order_id=order_id,
                    customer_id=customer_id,
                    currency=Currency.USD,
                )
                await self.uow.orders.add(order)

            order.add_line(
                sku=SkuId(sku),
                unit_price=Money(Decimal(price_amount), Currency.USD),
                quantity=quantity,
            )
            order.submit()

            # Atomically commit aggregate state
            await self.uow.commit()

            # Pull recorded domain events and publish over event bus
            events = order.pull_events()
            await self.dispatcher.dispatch(events)

            return order.id

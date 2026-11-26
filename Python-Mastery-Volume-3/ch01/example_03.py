# domain/model.py
"""Domain entities, value objects, and aggregate roots for Order Processing.

Pure Python 3.12+ implementation with zero external framework dependencies.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum
from typing import NewType, Sequence
import uuid


OrderId = NewType("OrderId", uuid.UUID)
SkuId = NewType("SkuId", str)


class Currency(StrEnum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    INR = "INR"


class OrderStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    CANCELLED = "CANCELLED"
    FULFILLED = "FULFILLED"


class DomainError(Exception):
    """Base domain exception for all domain invariant violations."""


class CurrencyMismatchError(DomainError):
    """Raised when arithmetic operations are attempted across divergent currencies."""


class InvariantViolationError(DomainError):
    """Raised when an aggregate state transition violates business rules."""


@dataclass(frozen=True, slots=True)
class Money:
    """Immutable monetary Value Object enforcing arithmetic consistency."""

    amount: Decimal
    currency: Currency

    def __post_init__(self) -> None:
        if self.amount < Decimal("0.00"):
            raise InvariantViolationError(f"Monetary amount cannot be negative: {self.amount}")

    def add(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise CurrencyMismatchError(
                f"Cannot add mismatched currencies: {self.currency} and {other.currency}"
            )
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def multiply(self, factor: int) -> Money:
        if factor < 0:
            raise InvariantViolationError(f"Multiplication factor cannot be negative: {factor}")
        return Money(amount=self.amount * Decimal(factor), currency=self.currency)


@dataclass(frozen=True, slots=True)
class OrderLine:
    """Internal entity representing an itemized product within an order."""

    line_id: uuid.UUID
    sku: SkuId
    unit_price: Money
    quantity: int

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise InvariantViolationError(f"Line item quantity must be positive: {self.quantity}")

    @property
    def total(self) -> Money:
        return self.unit_price.multiply(self.quantity)


@dataclass(frozen=True, slots=True)
class DomainEvent:
    """Base record for all published domain state notifications."""

    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True, slots=True)
class OrderSubmittedEvent(DomainEvent):
    order_id: OrderId = field(default=None)  # type: ignore[assignment]
    customer_id: uuid.UUID = field(default=None)  # type: ignore[assignment]
    total_amount: Decimal = Decimal("0.00")
    currency: str = "USD"


@dataclass(frozen=True, slots=True)
class OrderCancelledEvent(DomainEvent):
    order_id: OrderId = field(default=None)  # type: ignore[assignment]
    reason: str = ""


class OrderAggregate:
    """Aggregate Root managing transactional order boundaries and invariants."""

    def __init__(self, order_id: OrderId, customer_id: uuid.UUID, currency: Currency) -> None:
        self.id = order_id
        self.customer_id = customer_id
        self.currency = currency
        self.status = OrderStatus.DRAFT
        self._lines: list[OrderLine] = []
        self._events: list[DomainEvent] = []

    @property
    def lines(self) -> Sequence[OrderLine]:
        return tuple(self._lines)

    @property
    def total(self) -> Money:
        total_money = Money(Decimal("0.00"), self.currency)
        for line in self._lines:
            total_money = total_money.add(line.total)
        return total_money

    def add_line(self, sku: SkuId, unit_price: Money, quantity: int) -> None:
        if self.status != OrderStatus.DRAFT:
            raise InvariantViolationError(
                f"Cannot modify order in state '{self.status}'. Must be DRAFT."
            )
        if unit_price.currency != self.currency:
            raise CurrencyMismatchError(
                f"Item currency {unit_price.currency} does not match order currency {self.currency}"
            )

        # Invariant: Maximum allowable aggregate lines = 50
        if len(self._lines) >= 50:
            raise InvariantViolationError("Order exceeds maximum capacity of 50 distinct lines.")

        line = OrderLine(
            line_id=uuid.uuid4(),
            sku=sku,
            unit_price=unit_price,
            quantity=quantity,
        )
        self._lines.append(line)

    def submit(self) -> None:
        if self.status != OrderStatus.DRAFT:
            raise InvariantViolationError(f"Cannot submit order in status '{self.status}'.")
        if not self._lines:
            raise InvariantViolationError("Cannot submit empty order with zero line items.")

        # Invariant: Maximum single-order checkout cap = $100,000
        if self.total.amount > Decimal("100000.00"):
            raise InvariantViolationError("Order exceeds maximum allowable threshold ($100,000.00).")

        self.status = OrderStatus.SUBMITTED
        self._events.append(
            OrderSubmittedEvent(
                order_id=self.id,
                customer_id=self.customer_id,
                total_amount=self.total.amount,
                currency=self.currency.value,
            )
        )

    def cancel(self, reason: str) -> None:
        if self.status == OrderStatus.FULFILLED:
            raise InvariantViolationError("Cannot cancel an already fulfilled order.")

        self.status = OrderStatus.CANCELLED
        self._events.append(
            OrderCancelledEvent(order_id=self.id, reason=reason)
        )

    def pull_events(self) -> list[DomainEvent]:
        events = list(self._events)
        self._events.clear()
        return events

from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal
import uuid

from sqlalchemy import ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Abstract base class establishing common metadata and type conventions."""
    pass


class OrderModel(Base):
    """Enterprise Order database record with strict type annotations."""
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Fully typed relationship declaration with explicit loading contract
    line_items: Mapped[list[OrderLineModel]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="raise",  # CRITICAL: Prevent accidental synchronous lazy loads
    )


class OrderLineModel(Base):
    __tablename__ = "order_lines"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    sku: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    order: Mapped[OrderModel] = relationship(back_populates="line_items")

# gateway/schemas.py
"""High-performance schema validation engine utilizing Pydantic V2 discriminated unions."""

from __future__ import annotations
from decimal import Decimal
from typing import Annotated, Literal, Union
import uuid

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

# Semantic constrained types
CleanString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=256)]
PositiveCurrency = Annotated[Decimal, Field(gt=Decimal("0.00"), decimal_places=2)]


class BaseEvent(BaseModel):
    """Immutable base event containing common distributed metadata."""
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",  # Strictly reject unauthorized additional fields
        str_strip_whitespace=True,
    )
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)


class CreditCardTransaction(BaseEvent):
    channel: Literal["CREDIT_CARD"] = "CREDIT_CARD"
    pan_last_four: Annotated[str, StringConstraints(pattern=r"^[0-9]{4}$")]
    auth_code: CleanString
    amount: PositiveCurrency


class BankTransferTransaction(BaseEvent):
    channel: Literal["BANK_TRANSFER"] = "BANK_TRANSFER"
    iban: CleanString
    routing_number: CleanString
    amount: PositiveCurrency


class CryptoSettlementTransaction(BaseEvent):
    channel: Literal["CRYPTO"] = "CRYPTO"
    network: Literal["ETHEREUM", "BITCOIN", "POLYGON"]
    tx_hash: CleanString
    amount: PositiveCurrency


# Discriminated Union: Pydantic inspects the 'channel' field to route validation directly
# to the target model in Rust without attempting trial-and-error deserialization.
TransactionPayload = Annotated[
    Union[CreditCardTransaction, BankTransferTransaction, CryptoSettlementTransaction],
    Field(discriminator="channel"),
]


class IngestionBatchRequest(BaseModel):
    """Batch payload submitted to the ingestion gateway."""
    model_config = ConfigDict(frozen=True)
    batch_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    transactions: list[TransactionPayload] = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def verify_batch_limits(self) -> "IngestionBatchRequest":
        """Enforces aggregate batch business rules across heterogeneous union records."""
        total_volume = sum(t.amount for t in self.transactions)
        if total_volume > Decimal("1000000.00"):
            raise ValueError(
                f"Batch total volume (${total_volume:,.2f}) exceeds per-batch ceiling of $1,000,000.00."
            )
        return self

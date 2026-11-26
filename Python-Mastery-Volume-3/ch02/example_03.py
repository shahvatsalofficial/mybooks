from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, Literal
import uuid
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
    StringConstraints,
)

# Constrained types enforced via Annotated metadata
NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
PositiveAmount = Annotated[Decimal, Field(gt=Decimal("0.00"), decimal_places=2)]

class BaseEnterpriseSchema(BaseModel):
    """Immutable, strictly typed base schema for enterprise DTOs."""
    model_config = ConfigDict(
        frozen=True,                    # Enforce immutability
        populate_by_name=True,          # Support camelCase aliases
        str_strip_whitespace=True,      # Automatically sanitize string inputs
        validate_assignment=True,       # Prevent illegal post-init mutation
        use_enum_values=True,           # Serialize enums to raw values
    )

class PaymentMethodDTO(BaseEnterpriseSchema):
    method_type: Literal["CARD", "WIRE", "CRYPTO"]
    token: NonEmptyString

class ProcessPaymentCommand(BaseEnterpriseSchema):
    transaction_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    amount: PositiveAmount
    currency: Literal["USD", "EUR", "GBP"]
    payment_method: PaymentMethodDTO
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        """Field validator executing in 'before' mode prior to core type checking."""
        if isinstance(value, str):
            return value.upper().strip()
        return value

    @model_validator(mode="after")
    def verify_payment_routing(self) -> "ProcessPaymentCommand":
        """Model validator executing in 'after' mode across the entire validated struct."""
        if self.payment_method.method_type == "WIRE" and self.amount < Decimal("1000.00"):
            raise ValueError("Wire transfers must meet a minimum processing threshold of $1,000.00.")
        return self

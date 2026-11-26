from typing import Literal, Union
from dataclasses import dataclass

@dataclass(frozen=True)
class PaymentInitiated:
    event_type: Literal["PAYMENT_INITIATED"]
    payment_id: str
    amount_usd: float

@dataclass(frozen=True)
class PaymentAuthorized:
    event_type: Literal["PAYMENT_AUTHORIZED"]
    payment_id: str
    auth_token: str

@dataclass(frozen=True)
class PaymentSettled:
    event_type: Literal["PAYMENT_SETTLED"]
    payment_id: str
    settled_at_epoch: int

@dataclass(frozen=True)
class PaymentFailed:
    event_type: Literal["PAYMENT_FAILED"]
    payment_id: str
    decline_code: str

# Discriminated Union Type Alias
type PaymentEvent = (
    PaymentInitiated
    | PaymentAuthorized
    | PaymentSettled
    | PaymentFailed
)

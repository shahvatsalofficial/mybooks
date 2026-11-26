# Hardened Pydantic schema enforcing ISO Currency enum
from enum import Enum
from pydantic import BaseModel, Field

class ISOCurrency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CHF = "CHF"
    JPY = "JPY"

class FXTradeSchema(BaseModel):
    base_currency: ISOCurrency = Field(..., description="ISO-4217 3-letter currency code")
    quote_currency: ISOCurrency = Field(..., description="ISO-4217 3-letter currency code")
    amount_cents: int = Field(..., gt=0, lt=1000000000, description="Amount in cents")

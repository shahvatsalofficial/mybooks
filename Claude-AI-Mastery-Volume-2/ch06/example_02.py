from pydantic import BaseModel, Field, field_validator, model_validator

class TradeOrderInput(BaseModel):
    account_id: str = Field(..., regex=r"^ACC-[0-9]{6}$", description="Customer trading account identifier")
    symbol: str = Field(..., description="Equity ticker symbol in uppercase (e.g. AAPL, MSFT)")
    order_type: str = Field(..., description="Execution type: LIMIT or MARKET")
    limit_price: float | None = Field(default=None, description="Mandatory for LIMIT orders, in USD")
    quantity: int = Field(..., gt=0, le=10000, description="Number of shares to execute")

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        return v.strip().upper()

    @model_validator(mode="after")
    def verify_limit_price_present(self) -> "TradeOrderInput":
        if self.order_type == "LIMIT" and self.limit_price is None:
            raise ValueError("limit_price is strictly mandatory when order_type is 'LIMIT'")
        return self

from typing import Union, Literal, Annotated
from pydantic import BaseModel, Field, ConfigDict

class FraudAlertEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_type: Literal["FRAUD_ALERT"] = "FRAUD_ALERT"
    severity: Literal["LOW", "MEDIUM", "CRITICAL"]
    suspect_ip: str
    risk_score: float

class WireTransferEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_type: Literal["WIRE_TRANSFER"] = "WIRE_TRANSFER"
    amount_usd: float
    source_iban: str
    destination_iban: str

class AccountStatusUpdateEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_type: Literal["ACCOUNT_STATUS"] = "ACCOUNT_STATUS"
    account_id: str
    new_status: Literal["ACTIVE", "SUSPENDED", "FROZEN"]

# Tagged Discriminator Union
EnterpriseSecurityEvent = Annotated[
    Union[FraudAlertEvent, WireTransferEvent, AccountStatusUpdateEvent],
    Field(discriminator="event_type")
]

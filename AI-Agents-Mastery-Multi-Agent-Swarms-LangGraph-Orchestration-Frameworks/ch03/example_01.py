from typing import Annotated, Any, Dict, List, Literal, Optional
from typing_extensions import TypedDict
import operator
from pydantic import BaseModel, Field

# 1. Global Parent State Schema
class GlobalParentState(TypedDict):
    ticket_id: str
    customer_tier: Literal["standard", "enterprise"]
    messages: Annotated[List[str], operator.add]
    active_route: str
    resolution_status: Literal["pending", "resolved", "escalated"]
    final_resolution_summary: Optional[str]

# 2. Private Subgraph State Schema: Billing Domain
class BillingSubgraphState(TypedDict):
    invoice_id: str
    customer_tier: str
    billing_logs: List[str]
    refund_amount_cents: int
    refund_authorized: bool
    billing_summary: str

# 3. Private Subgraph State Schema: Tech Support Domain
class TechSupportSubgraphState(TypedDict):
    service_name: str
    error_code: str
    diagnostic_traces: List[str]
    remediation_action: str
    tech_summary: str

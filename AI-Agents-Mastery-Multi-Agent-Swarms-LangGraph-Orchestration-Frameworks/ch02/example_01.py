from typing import Annotated, Any, Dict, List, Literal, Optional
from typing_extensions import TypedDict
import operator
from pydantic import BaseModel, Field

# 1. Structured Validation Models
class AuditFeedback(BaseModel):
    passed: bool = Field(description="True if artifact meets all engineering criteria")
    critique: str = Field(description="Actionable remediation steps if failed")
    severity: Literal["low", "medium", "critical"] = "low"

# 2. Graph State Schema with Annotated Reducers
class ResearchGraphState(TypedDict):
    topic: str
    draft_content: str
    audit_notes: Annotated[List[str], operator.add] # Appends feedback rather than overwriting
    revision_count: int
    is_approved: bool
    final_output: Optional[str]

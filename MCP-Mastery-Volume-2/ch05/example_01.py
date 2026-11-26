import operator
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """Core state object passed between all LangGraph nodes."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    session_id: str
    tenant_id: str
    requires_human_approval: bool

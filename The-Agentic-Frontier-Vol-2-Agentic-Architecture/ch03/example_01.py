from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
import operator

def append_messages(left: Sequence[BaseMessage], right: Sequence[BaseMessage]) -> Sequence[BaseMessage]:
    """Reducer function to append new agent messages while preserving history."""
    return list(left) + list(right)

class SquadState(TypedDict):
    """Immutable state container for multi-agent software engineering squad."""
    messages: Annotated[Sequence[BaseMessage], append_messages]
    next_step: str
    code_artifacts: dict[str, str]
    build_status: str
    retry_count: int

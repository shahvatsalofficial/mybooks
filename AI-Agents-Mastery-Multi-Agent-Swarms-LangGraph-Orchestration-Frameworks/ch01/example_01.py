from __future__ import annotations
import enum
import json
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Protocol, Union
from pydantic import BaseModel, Field

class AgentRole(str, enum.Enum):
    SUPERVISOR = "supervisor"
    RESEARCHER = "researcher"
    CODER = "coder"
    AUDITOR = "auditor"

class MessageType(str, enum.Enum):
    TASK_ASSIGNMENT = "task_assignment"
    TASK_RESULT = "task_result"
    CRITIQUE = "critique"
    TERMINATION = "termination"
    ERROR = "error"

class AgentMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    sender: str
    sender_role: AgentRole
    recipient: str
    message_type: MessageType
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    parent_id: Optional[str] = None

class AgentProtocol(Protocol):
    name: str
    role: AgentRole
    
    def process_message(self, message: AgentMessage) -> AgentMessage:
        ...

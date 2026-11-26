import hashlib
import json
import time
import uuid
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field

class A2ASecurityHeader(BaseModel):
    classification: Literal["public", "internal", "confidential", "restricted"] = "internal"
    signing_algorithm: str = "sha256-mock"
    signature: str
    expires_at: float

class A2ARoutingHeader(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    root_trace_id: str
    parent_id: Optional[str] = None
    hop_count: int = Field(default=0, ge=0, le=10)
    sender_uri: str
    recipient_uri: str

class A2AMessageEnvelope(BaseModel):
    protocol_version: str = "A2A/1.0"
    routing: A2ARoutingHeader
    security: A2ASecurityHeader
    intent: Literal["TASK_REQUEST", "TASK_RESPONSE", "EVENT_BROADCAST", "HANDOFF_COMMAND", "ERROR"]
    payload_schema: str = "urn:schema:generic_task_v1"
    payload: Dict[str, Any]

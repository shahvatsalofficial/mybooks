import time
import uuid
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class VersionedState(BaseModel):
    state_id: str
    version: int = Field(default=1, ge=1)
    data: Dict[str, Any]
    last_updated_by: str
    last_updated_at: float = Field(default_factory=time.time)

class StateConflictError(Exception):
    """Raised when an optimistic concurrency update collides with a newer version."""
    pass

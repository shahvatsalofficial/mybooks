import contextvars
from dataclasses import dataclass
import uuid

@dataclass(frozen=True, slots=True)
class SecurityContext:
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    roles: frozenset[str]
    scopes: frozenset[str]

# Global ContextVar maintaining task-isolated security credentials
current_security_context: contextvars.ContextVar[SecurityContext | None] = contextvars.ContextVar(
    "current_security_context",
    default=None,
)

from typing import dataclass_transform, Callable, TypeVar

T = TypeVar('T')

@dataclass_transform(
    kw_only_default=True,
    order_default=True,
    field_specifiers=()
)
def enterprise_model(cls: type[T]) -> type[T]:
    """Custom enterprise entity decorator recognized natively by Mypy and Pyright."""
    # Metaprogramming logic generating slots, validators, and serialization...
    return cls

@enterprise_model
class AuditLogEntry:
    timestamp_epoch: int
    actor_id: str
    action_payload: dict[str, str]

# Mypy strictly understands that AuditLogEntry has an auto-generated __init__:
# AuditLogEntry(timestamp_epoch=1710000000, actor_id="admin", action_payload={})
# Keyword arguments are fully checked, and omitting required fields is flagged!

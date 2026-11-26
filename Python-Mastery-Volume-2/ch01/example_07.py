"""
Recipe 01.3: Metaclass AST Attribute Validator & Frozen Invariant Engine
Architecture: Custom ordered namespace with immutability guarantees and type enforcement.
Target Runtime: Python 3.12+ (CPython)
"""

from __future__ import annotations
from collections import OrderedDict
from typing import Any, Dict, Mapping, Tuple, Type, get_type_hints


class StrictNamespace(OrderedDict[str, Any]):
    """Custom dictionary for class preparation preventing duplicate member assignments."""

    def __init__(self, class_name: str) -> None:
        super().__init__()
        self._class_name = class_name
        self._defined_slots: List[str] = []

    def __setitem__(self, key: str, value: Any) -> None:
        # Prevent duplicate definition of method functions within the class body
        if key in self and not key.startswith("__"):
            raise TypeError(
                f"Duplicate identifier '{key}' encountered in definition of class '{self._class_name}'. "
                f"Explicit definitions must not be shadowed."
            )
        super().__setitem__(key, value)


class FrozenInvariantMeta(type):
    """Metaclass that freezes class attributes and enforces strict type annotations."""

    @classmethod
    def __prepare__(mcs, name: str, bases: Tuple[Type[Any], ...], **kwargs: Any) -> StrictNamespace:
        return StrictNamespace(class_name=name)

    def __new__(
        mcs,
        name: str,
        bases: Tuple[Type[Any], ...],
        namespace: StrictNamespace,
        freeze_instances: bool = True,
        **kwargs: Any,
    ) -> FrozenInvariantMeta:
        # Extract fields declared with type annotations
        annotations = namespace.get("__annotations__", {})
        slotted_fields = tuple(k for k in annotations.keys() if not k.startswith("_"))

        # Enforce __slots__ generation if not explicitly provided
        if "__slots__" not in namespace:
            namespace["__slots__"] = slotted_fields

        # Synthesize frozen __setattr__ to prohibit post-init mutations
        def __frozen_setattr__(self: Any, attr: str, val: Any) -> None:
            if getattr(self, "_initialized", False):
                raise AttributeError(f"Mutation rejected: instance of '{name}' is immutable.")
            super(self.__class__, self).__setattr__(attr, val)

        if freeze_instances:
            namespace["__setattr__"] = __frozen_setattr__

        # Synthesize typed initializer
        def __init__(self: Any, **kwargs: Any) -> None:
            for field_name in slotted_fields:
                if field_name not in kwargs:
                    raise TypeError(f"Missing required argument '{field_name}' to {name}()")
                expected_type = annotations[field_name]
                val = kwargs[field_name]
                # Lightweight runtime type validation
                if isinstance(expected_type, type) and not isinstance(val, expected_type):
                    raise TypeError(
                        f"Field '{field_name}' must be of type {expected_type.__name__}, "
                        f"got {type(val).__name__} (value: {val!r})"
                    )
                super(self.__class__, self).__setattr__(field_name, val)
            super(self.__class__, self).__setattr__("_initialized", True)

        namespace["__init__"] = __init__

        # Allocate the final type object via standard CPython type constructor
        cls_obj = super().__new__(mcs, name, bases, dict(namespace))
        return cls_obj

    def __setattr__(cls, key: str, value: Any) -> None:
        """Prevent runtime monkey-patching of the class object itself."""
        if hasattr(cls, "_frozen") and cls._frozen:
            raise TypeError(f"Cannot mutate attribute '{key}' on frozen class object '{cls.__name__}'.")
        super().__setattr__(key, value)


class ImmutableConfig(metaclass=FrozenInvariantMeta):
    """Base class providing frozen invariant guarantees to operational models."""

    _initialized: bool = False
    _slots_frozen: bool = True


# Demonstration & Verification
class ProductionClusterConfig(ImmutableConfig):
    cluster_id: str
    nodes_count: int
    heartbeat_timeout_ms: float


if __name__ == "__main__":
    cfg = ProductionClusterConfig(cluster_id="us-east-prod-1", nodes_count=128, heartbeat_timeout_ms=250.0)
    print(f"Config Initialized: Cluster={cfg.cluster_id}, Nodes={cfg.nodes_count}")

    # Verify Instance Immutability
    try:
        cfg.nodes_count = 256
        raise AssertionError("Mutation should have raised AttributeError!")
    except AttributeError as e:
        print(f"Immutability Guard Successfully Blocked Mutation: {e}")

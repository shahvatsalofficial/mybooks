"""
Recipe 01.1: Thread-Safe Dynamic Class Factory with Type Constructors
Architecture: Zero-exec, slot-optimized dynamic class generator with caching.
Target Runtime: Python 3.12+ (CPython)
"""

from __future__ import annotations
import threading
from typing import Any, Callable, Dict, Mapping, Sequence, Tuple, Type


class ClassFactoryRegistry:
    """Thread-safe registry and cache for dynamically constructed type objects."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._cache: Dict[str, Type[Any]] = {}

    def build_record_type(
        self,
        class_name: str,
        fields: Sequence[str],
        base_classes: Tuple[Type[Any], ...] = (),
        validators: Mapping[str, Callable[[Any], bool]] | None = None,
    ) -> Type[Any]:
        """Synthesizes a slotted, thread-safe class using raw type constructor semantics.
        
        Args:
            class_name: Identifies the generated class in tracebacks.
            fields: Ordered sequence of string attribute names.
            base_classes: Tuple of base classes to inherit from.
            validators: Optional dictionary mapping field names to boolean predicates.
            
        Returns:
            A new, fully compiled Python type object with __slots__ enabled.
        """
        cache_key = f"{class_name}_{':'.join(sorted(fields))}"
        with self._lock:
            if cache_key in self._cache:
                return self._cache[cache_key]

            # Construct namespace dictionary with slotted memory layout
            slots = tuple(fields)
            namespace: Dict[str, Any] = {
                "__slots__": slots,
                "__doc__": f"Dynamically generated record class '{class_name}'.",
                "_validators": dict(validators) if validators else {},
            }

            # Inject synthesized __init__
            def __init__(self: Any, *args: Any, **kwargs: Any) -> None:
                if len(args) > len(slots):
                    raise TypeError(
                        f"__init__() takes at most {len(slots)} positional arguments ({len(args)} given)"
                    )
                # Assign positional arguments
                for name, value in zip(slots, args):
                    kwargs[name] = value

                # Validate and assign all attributes
                for name in slots:
                    if name not in kwargs:
                        raise ValueError(f"Missing required field '{name}' for '{class_name}'")
                    val = kwargs[name]
                    if self._validators and name in self._validators:
                        predicate = self._validators[name]
                        if not predicate(val):
                            raise TypeError(f"Validation failed for field '{name}' with value {val!r}")
                    setattr(self, name, val)

            # Inject synthesized __repr__
            def __repr__(self: Any) -> str:
                attrs = ", ".join(f"{s}={getattr(self, s)!r}" for s in self.__slots__)
                return f"{self.__class__.__name__}({attrs})"

            # Inject synthesized __eq__
            def __eq__(self: Any, other: Any) -> bool:
                if not isinstance(other, self.__class__):
                    return False
                return all(getattr(self, s) == getattr(other, s) for s in self.__slots__)

            namespace["__init__"] = __init__
            namespace["__repr__"] = __repr__
            namespace["__eq__"] = __eq__

            # Direct invocation of type constructor: type(name, bases, dict)
            new_type = type(class_name, base_classes, namespace)
            self._cache[cache_key] = new_type
            return new_type


# Demonstration & Verification
if __name__ == "__main__":
    factory = ClassFactoryRegistry()
    OrderRecord = factory.build_record_type(
        class_name="OrderRecord",
        fields=["order_id", "symbol", "quantity", "price"],
        validators={
            "quantity": lambda q: isinstance(q, int) and q > 0,
            "price": lambda p: isinstance(p, (float, int)) and p > 0.0,
        },
    )

    order = OrderRecord(order_id="ORD-9021", symbol="NVDA", quantity=100, price=142.50)
    print(f"Generated Record: {order}")
    assert order.symbol == "NVDA"
    assert order.__slots__ == ("order_id", "symbol", "quantity", "price")

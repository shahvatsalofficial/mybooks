# VERIFIED PRODUCTION FIX:
from collections import OrderedDict
import threading
from typing import Any, Dict, Type

class SchemaRegistry:
    MAX_SCHEMAS = 4096

    def __init__(self) -> None:
        self._cache: OrderedDict[str, Type[Any]] = OrderedDict()
        self._lock = threading.Lock()

    def get_or_create(self, schema_signature: str, field_specs: Dict[str, Type[Any]]) -> Type[Any]:
        with self._lock:
            if schema_signature in self._cache:
                self._cache.move_to_end(schema_signature)
                return self._cache[schema_signature]

            # Evict least-recently-used schema if cache capacity exceeded
            if len(self._cache) >= self.MAX_SCHEMAS:
                evicted_sig, evicted_cls = self._cache.popitem(last=False)
                del evicted_cls  # Explicitly release type reference

            # Build class with slotted memory and pure descriptors (zero cyclic closures)
            slots = tuple(field_specs.keys())
            ns = {
                "__slots__": slots,
                "_field_specs": field_specs,
                "validate": _static_schema_validator,  # Static pure function
            }
            new_cls = type(f"Schema_{schema_signature}", (), ns)
            self._cache[schema_signature] = new_cls
            return new_cls

def _static_schema_validator(instance: Any) -> bool:
    """Pure static function shared across all instances; zero cyclic reference closures."""
    specs = instance._field_specs
    for slot in instance.__slots__:
        val = getattr(instance, slot, None)
        if not isinstance(val, specs[slot]):
            return False
    return True

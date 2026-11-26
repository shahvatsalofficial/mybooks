"""
Recipe 01.2: Enterprise Plugin Registration via __init_subclass__
Architecture: Metaclass-free cooperative plugin discovery and contract enforcement.
Target Runtime: Python 3.12+ (CPython)
"""

from __future__ import annotations
import abc
import re
from typing import ClassVar, Dict, List, Type


class PluginContractError(TypeError):
    """Raised when a subclass fails to honor plugin architectural contracts."""


class PluginRegistryBase(abc.ABC):
    """Cooperative root base class for enterprise pluggable micro-kernels."""

    _REGISTRY: ClassVar[Dict[str, Type[PluginRegistryBase]]] = {}
    _SEMVER_REGEX: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)$"
    )

    plugin_id: ClassVar[str]
    plugin_version: ClassVar[str]

    def __init_subclass__(
        cls,
        plugin_id: str | None = None,
        version: str = "1.0.0",
        abstract: bool = False,
        **kwargs: object,
    ) -> None:
        """Cooperative subclass registration and contract validation."""
        super().__init_subclass__(**kwargs)

        # Skip validation if intermediate base is explicitly declared abstract
        if abstract:
            return

        if not plugin_id:
            raise PluginContractError(
                f"Subclass '{cls.__name__}' must specify a non-empty 'plugin_id' keyword argument."
            )

        if not cls._SEMVER_REGEX.match(version):
            raise PluginContractError(
                f"Plugin '{plugin_id}' declared version '{version}', which is not valid SemVer (e.g. '1.2.0')."
            )

        if plugin_id in cls._REGISTRY:
            existing = cls._REGISTRY[plugin_id]
            raise PluginContractError(
                f"Duplicate plugin registration conflict: '{plugin_id}' already registered by '{existing.__qualname__}'."
            )

        # Enforce required abstract interface methods
        abstract_methods = getattr(cls, "__abstractmethods__", set())
        if abstract_methods:
            missing = ", ".join(sorted(abstract_methods))
            raise PluginContractError(
                f"Cannot register plugin '{plugin_id}': concrete methods missing for: {missing}"
            )

        cls.plugin_id = plugin_id
        cls.plugin_version = version
        cls._REGISTRY[plugin_id] = cls

    @classmethod
    def get_plugin(cls, plugin_id: str) -> Type[PluginRegistryBase]:
        """Resolves an active plugin from the central registry."""
        if plugin_id not in cls._REGISTRY:
            raise KeyError(f"Plugin '{plugin_id}' is not loaded. Registered: {list(cls._REGISTRY.keys())}")
        return cls._REGISTRY[plugin_id]

    @classmethod
    def list_plugins(cls) -> List[str]:
        """Returns all registered plugin identifiers."""
        return sorted(cls._REGISTRY.keys())

    @abc.abstractmethod
    def execute_payload(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mandatory execution interface for concrete plugins."""


# Concrete Implementation Example
class FastGzipCompressionPlugin(PluginRegistryBase, plugin_id="compress.gzip", version="2.1.0"):
    """Production implementation of gzip compression service."""

    def execute_payload(self, context: Dict[str, Any]) -> Dict[str, Any]:
        payload: bytes = context.get("data", b"")
        import gzip
        compressed = gzip.compress(payload, compresslevel=6)
        return {"status": "SUCCESS", "bytes_out": len(compressed), "payload": compressed}


if __name__ == "__main__":
    assert "compress.gzip" in PluginRegistryBase.list_plugins()
    plugin_cls = PluginRegistryBase.get_plugin("compress.gzip")
    instance = plugin_cls()
    result = instance.execute_payload({"data": b"High-frequency algorithmic trading telemetry stream"})
    print(f"Plugin Execution Result: {result['status']}, Size: {result['bytes_out']} bytes")

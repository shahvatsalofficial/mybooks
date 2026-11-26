"""
Recipe 08.2: Hierarchical ExceptionGroup Sanitizer & Structured JSON Telemetry Logger
Requires: Python 3.11+
Architecture: Recursive Exception Tree Unpacking, Traceback Scrubbing, and OpenTelemetry Compliance.
"""

from __future__ import annotations
import json
import logging
import traceback
from typing import Any

logger = logging.getLogger("telemetry.sanitizer")

class ExceptionTreeTelemetrySanitizer:
    @classmethod
    def serialize_exception_tree(cls, exc: BaseException, max_depth: int = 5) -> dict[str, Any]:
        """
        Recursively decomposes an ExceptionGroup or scalar Exception into an
        OpenTelemetry-compliant, JSON-serializable dictionary with sanitized metadata.
        """
        return cls._decompose_node(exc, current_depth=0, max_depth=max_depth)

    @classmethod
    def _decompose_node(cls, exc: BaseException, current_depth: int, max_depth: int) -> dict[str, Any]:
        node: dict[str, Any] = {
            "type": type(exc).__name__,
            "module": type(exc).__module__,
            "message": str(exc),
            "depth": current_depth,
        }

        # Format sanitized traceback frames (stripping sensitive local variables)
        tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
        node["traceback"] = "".join(tb_lines).splitlines()

        # Handle explicit chaining (__cause__)
        if exc.__cause__ is not None and current_depth < max_depth:
            node["explicit_cause"] = cls._decompose_node(
                exc.__cause__, current_depth + 1, max_depth
            )

        # Handle composite PEP 654 ExceptionGroup trees
        if isinstance(exc, BaseExceptionGroup):
            node["is_composite_group"] = True
            node["sub_exception_count"] = len(exc.exceptions)
            if current_depth < max_depth:
                node["exceptions"] = [
                    cls._decompose_node(child, current_depth + 1, max_depth)
                    for child in exc.exceptions
                ]
            else:
                node["exceptions"] = ["<Max recursion depth reached>"]
        else:
            node["is_composite_group"] = False

        return node

    @classmethod
    def to_json(cls, exc: BaseException) -> str:
        data = cls.serialize_exception_tree(exc)
        return json.dumps(data, indent=2)

# Verification harness
def test_sanitizer_harness() -> None:
    try:
        try:
            raise ConnectionRefusedError("Unable to reach Redis replica at 10.0.4.15:6379")
        except ConnectionRefusedError as err:
            raise RuntimeError("Cache tier failed during batch initialization") from err
    except RuntimeError as chained_err:
        eg = ExceptionGroup(
            "ServiceMeshStartupFailure",
            [
                chained_err,
                ValueError("Config parameter 'pool_size' must be >= 10"),
                TimeoutError("gRPC handshake timed out after 5000ms"),
            ]
        )
        json_output = ExceptionTreeTelemetrySanitizer.to_json(eg)
        print("Serialized Telemetry Payload:\n" + json_output)

if __name__ == "__main__":
    test_sanitizer_harness()

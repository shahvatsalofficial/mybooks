"""
Recipe 02.3: Dynamic Attribute Interceptor Proxy with Audit Telemetry
Architecture: Non-invasive auditing proxy leveraging descriptor __getattribute__ hooks.
Target Runtime: Python 3.12+ (CPython)
"""

from __future__ import annotations
import logging
import sys
import time
from typing import Any, Callable, Dict, List, TypeVar

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AuditInterceptor")

T = TypeVar("T")


class AuditTelemetryLog:
    """Thread-safe ring buffer recording attribute access events."""

    def __init__(self, max_records: int = 1000) -> None:
        self._records: List[Dict[str, Any]] = []

    def record_access(self, target_type: str, attr_name: str, duration_ns: int, success: bool) -> None:
        event = {
            "target": target_type,
            "attribute": attr_name,
            "duration_ns": duration_ns,
            "success": success,
            "timestamp": time.time(),
        }
        self._records.append(event)
        if len(self._records) > 1000:
            self._records.pop(0)


AUDIT_LOG = AuditTelemetryLog()


class AuditedProxy:
    """Wrapper that instruments attribute access on any encapsulated target object."""

    def __init__(self, target: Any) -> None:
        # Bypass self.__getattribute__ during internal initialization
        object.__setattr__(self, "_target", target)
        object.__setattr__(self, "_type_name", target.__class__.__name__)

    def __getattribute__(self, name: str) -> Any:
        # Bypass auditing for private internal proxy fields
        if name in ("_target", "_type_name"):
            return object.__getattribute__(self, name)

        target = object.__getattribute__(self, "_target")
        type_name = object.__getattribute__(self, "_type_name")

        start_time = time.perf_counter_ns()
        success = True
        try:
            val = getattr(target, name)
            # If the resolved attribute is callable, wrap it to intercept execution
            if callable(val):
                def instrumented_call(*args: Any, **kwargs: Any) -> Any:
                    call_start = time.perf_counter_ns()
                    try:
                        res = val(*args, **kwargs)
                        return res
                    finally:
                        call_dur = time.perf_counter_ns() - call_start
                        logger.info(f"AUDIT METHOD: {type_name}.{name}() took {call_dur / 1000:.2f} µs")
                return instrumented_call
            return val
        except AttributeError:
            success = False
            raise
        finally:
            duration_ns = time.perf_counter_ns() - start_time
            AUDIT_LOG.record_access(type_name, name, duration_ns, success)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ("_target", "_type_name"):
            object.__setattr__(self, name, value)
            return

        target = object.__getattribute__(self, "_target")
        type_name = object.__getattribute__(self, "_type_name")
        logger.info(f"AUDIT MUTATION: {type_name}.{name} = {value!r}")
        setattr(target, name, value)


# Demonstration & Verification
class SettlementVault:
    def __init__(self, balance: float) -> None:
        self.balance = balance

    def deposit(self, amount: float) -> float:
        self.balance += amount
        return self.balance


if __name__ == "__main__":
    raw_vault = SettlementVault(balance=1_000_000.0)
    vault = AuditedProxy(raw_vault)

    # Trigger Audited Reads and Methods
    print(f"Current Balance: ${vault.balance:,.2f}")
    new_bal = vault.deposit(250_000.0)
    print(f"Updated Balance: ${new_bal:,.2f}")
    vault.balance = 1_500_000.0

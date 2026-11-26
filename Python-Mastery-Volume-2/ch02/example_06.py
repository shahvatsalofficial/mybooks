"""
SingleFlight Request Coalescing Pattern for Descriptors
Ensures only one in-flight execution per key across concurrent worker threads.
"""

import threading
from typing import Any, Callable, Dict, Generic, TypeVar

T = TypeVar("T")

class SingleFlightGroup(Generic[T]):
    """Coalesces duplicate in-flight computations into a single execution."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._calls: Dict[str, _FlightCall[T]] = {}

    def execute(self, key: str, fn: Callable[[], T]) -> T:
        with self._lock:
            if key in self._calls:
                call = self._calls[key]
                # Another thread is already computing this key: release lock and wait
                call_lock = call.completed_event
            else:
                call = _FlightCall[T]()
                self._calls[key] = call
                call_lock = None

        if call_lock is not None:
            call_lock.wait()
            if call.error is not None:
                raise call.error
            return call.val  # type: ignore[return-value]

        # First thread: compute result and notify all waiting peers
        try:
            val = fn()
            call.val = val
            return val
        except Exception as e:
            call.error = e
            raise
        finally:
            with self._lock:
                del self._calls[key]
            call.completed_event.set()

class _FlightCall(Generic[T]):
    def __init__(self) -> None:
        self.val: T | None = None
        self.error: Exception | None = None
        self.completed_event = threading.Event()

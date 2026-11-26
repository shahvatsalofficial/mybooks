"""
Recipe 02.2: Thread-Safe Distributed Lazy-Evaluation Property Engine
Architecture: Mutex-guarded lazy property with TTL invalidation and stampede suppression.
Target Runtime: Python 3.12+ (CPython)
"""

from __future__ import annotations
import threading
import time
from typing import Any, Callable, Generic, TypeVar, Union, overload

T = TypeVar("T")


class ThreadSafeLazyProperty(Generic[T]):
    """Thread-safe, TTL-capable lazy property preventing thundering herd stampedes."""

    def __init__(self, func: Callable[[Any], T], ttl_seconds: float | None = None) -> None:
        self.func = func
        self.ttl_seconds = ttl_seconds
        self._name: str = func.__name__
        self._cache_field: str = f"_cached_{self._name}"
        self._ts_field: str = f"_cached_ts_{self._name}"
        self._lock_field: str = f"_lock_{self._name}"

    def __set_name__(self, owner: type, name: str) -> None:
        self._name = name
        self._cache_field = f"_cached_{name}"
        self._ts_field = f"_cached_ts_{name}"
        self._lock_field = f"_lock_{name}"

    @overload
    def __get__(self, instance: None, owner: type) -> ThreadSafeLazyProperty[T]: ...

    @overload
    def __get__(self, instance: object, owner: type | None = None) -> T: ...

    def __get__(self, instance: object | None, owner: type | None = None) -> Union[ThreadSafeLazyProperty[T], T]:
        if instance is None:
            return self

        # Fast path: check if cache is warm and still valid
        if hasattr(instance, self._cache_field):
            if self.ttl_seconds is None:
                return getattr(instance, self._cache_field)  # type: ignore[no-any-return]
            cached_ts: float = getattr(instance, self._ts_field, 0.0)
            if (time.monotonic() - cached_ts) < self.ttl_seconds:
                return getattr(instance, self._cache_field)  # type: ignore[no-any-return]

        # Slow path: resolve lock for double-checked locking pattern
        lock = self._get_or_create_lock(instance)
        with lock:
            # Re-check under lock to avoid duplicate compute (stampede suppression)
            if hasattr(instance, self._cache_field):
                if self.ttl_seconds is None:
                    return getattr(instance, self._cache_field)  # type: ignore[no-any-return]
                cached_ts = getattr(instance, self._ts_field, 0.0)
                if (time.monotonic() - cached_ts) < self.ttl_seconds:
                    return getattr(instance, self._cache_field)  # type: ignore[no-any-return]

            # Compute expensive value
            computed_value: T = self.func(instance)
            setattr(instance, self._cache_field, computed_value)
            setattr(instance, self._ts_field, time.monotonic())
            return computed_value

    def invalidate(self, instance: object) -> None:
        """Programmatically purges the cached value, forcing re-computation on next access."""
        lock = self._get_or_create_lock(instance)
        with lock:
            if hasattr(instance, self._cache_field):
                delattr(instance, self._cache_field)
            if hasattr(instance, self._ts_field):
                delattr(instance, self._ts_field)

    def _get_or_create_lock(self, instance: object) -> threading.Lock:
        """Retrieves or atomically creates the per-instance mutex."""
        if not hasattr(instance, self._lock_field):
            # Guard against simultaneous lock initialization
            with threading.Lock():
                if not hasattr(instance, self._lock_field):
                    setattr(instance, self._lock_field, threading.Lock())
        return getattr(instance, self._lock_field)  # type: ignore[no-any-return]


# Demonstration & Verification
class CryptographicKeystore:
    def __init__(self, key_id: str) -> None:
        self.key_id = key_id
        self.compute_count = 0

    @ThreadSafeLazyProperty
    def master_symmetric_key(self) -> bytes:
        """Simulates expensive key derivation function (e.g. Argon2id / PBKDF2)."""
        self.compute_count += 1
        time.sleep(0.05)  # Simulate expensive cryptographic expansion
        return b"\x8a\x9f\x12\x4c" * 8


if __name__ == "__main__":
    keystore = CryptographicKeystore(key_id="hsm-node-99")

    # Concurrent Thread-Access Test
    def worker() -> None:
        _ = keystore.master_symmetric_key

    threads = [threading.Thread(target=worker) for _ in range(16)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print(f"Master Key Length: {len(keystore.master_symmetric_key)} bytes")
    print(f"Total Computation Count: {keystore.compute_count} (Stampede Suppressed: Expected 1)")
    assert keystore.compute_count == 1

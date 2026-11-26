"""
Recipe 03.3: High-Density Slotted Weak Cache Engine
File: recipe_03_3_slotted_weak_cache.py
Python Version: 3.12+
"""

from __future__ import annotations
import gc
import sys
import weakref
from typing import Optional


class CompactSessionEntity:
    """Slotted session entity eliminating __dict__ overhead and supporting weakrefs."""

    # '__weakref__' slot enables weak referencing without restoring __dict__
    __slots__ = ("session_id", "user_id", "auth_token", "created_at", "__weakref__")

    def __init__(self, session_id: str, user_id: int, auth_token: str, created_at: int) -> None:
        self.session_id = session_id
        self.user_id = user_id
        self.auth_token = auth_token
        self.created_at = created_at


class NonLeakingSessionCache:
    """In-memory cache that automatically evicts entries when strong references expire."""

    def __init__(self) -> None:
        # WeakValueDictionary drops keys automatically when values are garbage-collected
        self._cache: weakref.WeakValueDictionary[str, CompactSessionEntity] = (
            weakref.WeakValueDictionary()
        )

    def put(self, session: CompactSessionEntity) -> None:
        self._cache[session.session_id] = session

    def get(self, session_id: str) -> Optional[CompactSessionEntity]:
        return self._cache.get(session_id)

    def active_sessions_count(self) -> int:
        return len(self._cache)


if __name__ == "__main__":
    cache = NonLeakingSessionCache()

    # 1. Create active sessions in a caller's scope
    active_tokens = []
    for i in range(100):
        s = CompactSessionEntity(f"sess-{i}", 1000 + i, f"tok-{i * 9}", 1710000000)
        cache.put(s)
        if i % 2 == 0:
            active_tokens.append(s)  # Retain strong reference to even sessions

    print(f"[*] Total sessions initially cached: {cache.active_sessions_count()}")

    # 2. Force garbage collection of local variables
    gc.collect()

    print(f"[*] Sessions retained after dropping odd references: {cache.active_sessions_count()}")
    assert cache.active_sessions_count() == 50
    print("[SUCCESS] WeakValueDictionary automatically evicted exactly 50 discarded sessions!")

    # Memory Size Benchmark
    sample_obj = active_tokens[0]
    print(f"[*] Size of Slotted Object Header: {sys.getsizeof(sample_obj)} bytes (vs 152B+ unslotted)")

"""
Recipe 05.3: Cyclic Reference Hunter with Finalizer Telemetry & Generational GC
Architecture: Introspects gc.get_objects() to diagnose reference loops and finalizer locks.
Target Runtime: Python 3.12+ (CPython)
"""

from __future__ import annotations
import gc
import sys
from typing import Any, Dict, List, Set, Tuple


class CyclicReferenceHunter:
    """Scans live heap objects to identify circular reference cycles and finalizers."""

    @staticmethod
    def inspect_uncollectable_cycles() -> List[Dict[str, Any]]:
        """Forces a full generational garbage collection sweep and checks for broken cycles."""
        # Enable GC debug flags temporarily to capture cycle metadata
        prev_flags = gc.get_debug()
        gc.set_debug(gc.DEBUG_UNCOLLECTABLE)
        try:
            # Force collection across all three generations (0, 1, 2)
            unreachable_count = gc.collect()
            uncollectable_objects = gc.garbage  # Objects that could not be freed

            results = []
            for obj in uncollectable_objects:
                info = {
                    "type": type(obj).__name__,
                    "id": hex(id(obj)),
                    "has_finalizer": hasattr(obj, "__del__"),
                    "referents_count": len(gc.get_referents(obj)),
                    "referrers_count": len(gc.get_referrers(obj)),
                }
                results.append(info)
            return results
        finally:
            gc.set_debug(prev_flags)

    @staticmethod
    def find_reference_cycle(target_obj: Any, max_depth: int = 10) -> Optional[List[str]]:
        """Performs Depth-First Search (DFS) on an object's referents to locate circular loops."""
        visited: Set[int] = set()
        path: List[Any] = []

        def dfs(current: Any, depth: int) -> bool:
            if depth > max_depth:
                return False
            curr_id = id(current)
            if curr_id in visited:
                if current in path:
                    # Circular reference detected!
                    path.append(current)
                    return True
                return False

            visited.add(curr_id)
            path.append(current)

            for referent in gc.get_referents(current):
                # Ignore module globals and type definitions
                if isinstance(referent, (dict, list, tuple, set)) or hasattr(referent, "__dict__"):
                    if dfs(referent, depth + 1):
                        return True

            path.pop()
            return False

        if dfs(target_obj, 0):
            return [f"{type(o).__name__} (0x{id(o):x})" for o in path]
        return None


# Demonstration & Verification
class NodeA:
    def __init__(self) -> None:
        self.peer: Optional[NodeB] = None


class NodeB:
    def __init__(self) -> None:
        self.peer: Optional[NodeA] = None


if __name__ == "__main__":
    # Create deliberate reference cycle
    a = NodeA()
    b = NodeB()
    a.peer = b
    b.peer = a

    hunter = CyclicReferenceHunter()
    cycle_path = hunter.find_reference_cycle(a)
    print("Cycle Path Detected:")
    if cycle_path:
        for step in cycle_path:
            print(f"  -> {step}")

    assert cycle_path is not None, "Cycle detector failed to find reference loop!"

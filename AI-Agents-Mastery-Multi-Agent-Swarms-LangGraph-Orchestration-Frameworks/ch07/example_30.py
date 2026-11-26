import uuid
import time
from typing import Dict, Any, Set, Tuple

class DistributedORSetCRDT:
    """State-based Observed-Removed Set (ORSet) for conflict-free cross-region state sync."""
    
    def __init__(self, region_id: str):
        self.region_id = region_id
        # Element -> Set of unique generation UUID tags
        self.add_set: Set[Tuple[str, str]] = set() # (element, tag)
        self.remove_set: Set[Tuple[str, str]] = set() # (element, tag)

    def add(self, element: str) -> str:
        tag = f"{self.region_id}::{uuid.uuid4().hex[:8]}"
        self.add_set.add((element, tag))
        print(f"[{self.region_id}] Added '{element}' with tag '{tag}'.")
        return tag

    def remove(self, element: str) -> None:
        # Move all currently observed tags for this element to the remove set
        matching_tags = {tag for elem, tag in self.add_set if elem == element}
        for tag in matching_tags:
            self.remove_set.add((element, tag))
        print(f"[{self.region_id}] Removed '{element}' (Tombstoned {len(matching_tags)} tags).")

    def read_active_elements(self) -> Set[str]:
        # Active elements = Elements with at least one tag in add_set not in remove_set
        active_tags = self.add_set - self.remove_set
        return {elem for elem, _ in active_tags}

    def merge_remote_state(self, remote_add_set: Set[Tuple[str, str]], remote_remove_set: Set[Tuple[str, str]]) -> None:
        """Lattice join: Union add sets and union remove sets."""
        before = len(self.read_active_elements())
        self.add_set.update(remote_add_set)
        self.remove_set.update(remote_remove_set)
        after = len(self.read_active_elements())
        print(f"[{self.region_id}] Lattice merged remote state: Elements updated ({before} -> {after} active).")

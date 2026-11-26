class GSetCRDT:
    """Grow-only Set CRDT for conflict-free state merging across distributed swarms."""
    def __init__(self, initial: set[str] = None):
        self._set = initial or set()

    def add(self, item: str):
        self._set.add(item)

    def merge(self, other: 'GSetCRDT') -> 'GSetCRDT':
        return GSetCRDT(self._set.union(other._set))

    @property
    def value(self) -> set[str]:
        return self._set.copy()

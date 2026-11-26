class ManagedResourceDescriptor:
    """Demonstrates deterministic resource reclamation via __delete__."""

    def __init__(self, resource_pool: ConnectionPool) -> None:
        self.pool = resource_pool
        self._attr = ""

    def __set_name__(self, owner: type, name: str) -> None:
        self._attr = f"_res_{name}"

    def __get__(self, instance: object | None, owner: type | None = None) -> Any:
        if instance is None:
            return self
        res = getattr(instance, self._attr, None)
        if res is None:
            res = self.pool.acquire()
            setattr(instance, self._attr, res)
        return res

    def __delete__(self, instance: object) -> None:
        res = getattr(instance, self._attr, None)
        if res is not None:
            self.pool.release(res)  # Deterministic return to pool
            delattr(instance, self._attr)

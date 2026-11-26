# Clean, readable, zero-boilerplate generics
class CacheRegistry[K: str, V]:
    def __init__(self) -> None:
        self._store: dict[K, V] = {}

    def get(self, key: K) -> V | None:
        return self._store.get(key)

def execute_batch[T, R](items: list[T], transform: Callable[[T], R]) -> list[R]:
    return [transform(item) for item in items]

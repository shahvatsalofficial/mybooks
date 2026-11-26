from __future__ import annotations


class IdempotencyReplayCache:
    def __init__(self, max_entries: int = 10_000) -> None:
        self.max_entries = max_entries
        self._seen: dict[str, int] = {}

    def accept_once(self, idempotency_key: str, epoch_sec: int) -> bool:
        if idempotency_key in self._seen:
            return False
        if len(self._seen) >= self.max_entries:
            oldest_key = next(iter(self._seen))
            self._seen.pop(oldest_key)
        self._seen[idempotency_key] = epoch_sec
        return True


if __name__ == "__main__":
    cache = IdempotencyReplayCache()
    print("First delivery:", cache.accept_once("8f20c41e9a3d7b12", 1_795_600_000))
    print("Duplicate webhook:", cache.accept_once("8f20c41e9a3d7b12", 1_795_600_012))

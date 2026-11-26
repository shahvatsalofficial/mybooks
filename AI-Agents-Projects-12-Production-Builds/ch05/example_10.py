from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from pydantic import BaseModel


class ExecutionResult(BaseModel):
    idempotency_key: str
    runbook_id: str
    executed: bool
    status: str
    duration_ms: float


@dataclass
class DistributedLeaseStore:
    leases: dict[str, float] = field(default_factory=dict)
    completed: dict[str, ExecutionResult] = field(default_factory=dict)

    def acquire(self, key: str, ttl_sec: float = 120.0) -> bool:
        now = time.monotonic()
        expiry = self.leases.get(key, 0.0)
        if expiry > now:
            return False
        self.leases[key] = now + ttl_sec
        return True

    def release(self, key: str) -> None:
        self.leases.pop(key, None)


class IdempotentRunbookExecutor:
    def __init__(self, store: DistributedLeaseStore) -> None:
        self.store = store

    async def execute(self, idempotency_key: str, runbook_id: str, target: str) -> ExecutionResult:
        if idempotency_key in self.store.completed:
            cached = self.store.completed[idempotency_key]
            return cached.model_copy(update={"executed": False, "status": "DEDUPLICATED_CACHED"})

        if not self.store.acquire(idempotency_key):
            return ExecutionResult(
                idempotency_key=idempotency_key,
                runbook_id=runbook_id,
                executed=False,
                status="LOCK_CONTENTION_SKIPPED",
                duration_ms=0.0,
            )

        start = time.perf_counter()
        try:
            await asyncio.sleep(0.025)
            elapsed_ms = round((time.perf_counter() - start) * 1000.0, 2)
            result = ExecutionResult(
                idempotency_key=idempotency_key,
                runbook_id=runbook_id,
                executed=True,
                status=f"ROLLED_BACK:{target}",
                duration_ms=elapsed_ms,
            )
            self.store.completed[idempotency_key] = result
            return result
        finally:
            self.store.release(idempotency_key)


async def main() -> None:
    executor = IdempotentRunbookExecutor(DistributedLeaseStore())
    key = "prod-payments:checkout-orchestrator:RB-ROLLBACK-DEPLOYMENT:rev42"
    first, second = await asyncio.gather(
        executor.execute(key, "RB-ROLLBACK-DEPLOYMENT", "checkout-orchestrator"),
        executor.execute(key, "RB-ROLLBACK-DEPLOYMENT", "checkout-orchestrator"),
    )
    print("Worker 1:", first.model_dump_json())
    print("Worker 2:", second.model_dump_json())


if __name__ == "__main__":
    asyncio.run(main())

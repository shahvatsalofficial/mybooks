from __future__ import annotations

import asyncio
from collections import deque
from pydantic import BaseModel


class DlqItem(BaseModel):
    idempotency_key: str
    record_id: str
    patch_payload: dict[str, object]
    attempts: int = 0
    last_error: str = ""


class SyncDlqWorker:
    def __init__(self, max_attempts: int = 3) -> None:
        self.max_attempts = max_attempts
        self.queue: deque[DlqItem] = deque()
        self.replayed: list[str] = []

    def enqueue(self, item: DlqItem) -> None:
        self.queue.append(item)

    async def process_batch(self, crm_healthy: bool) -> dict[str, int]:
        processed = 0
        requeued = 0
        count = len(self.queue)
        for _ in range(count):
            item = self.queue.popleft()
            await asyncio.sleep(0.005)
            if crm_healthy:
                self.replayed.append(item.idempotency_key)
                processed += 1
            else:
                item.attempts += 1
                if item.attempts < self.max_attempts:
                    self.queue.append(item)
                    requeued += 1
        return {"replayed": processed, "requeued": requeued}


async def main() -> None:
    worker = SyncDlqWorker()
    worker.enqueue(DlqItem(idempotency_key="8f20c41e9a3d7b12", record_id="OPP-90211", patch_payload={"meddic_score": 89}, last_error="429_RATE_LIMIT"))
    print("Outage pass:", await worker.process_batch(crm_healthy=False))
    print("Recovery pass:", await worker.process_batch(crm_healthy=True))


if __name__ == "__main__":
    asyncio.run(main())

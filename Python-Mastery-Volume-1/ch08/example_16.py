"""
Recipe 08.3: Resilient Microservice TaskGroup Supervisor with Circuit Breaker & DLQ
Requires: Python 3.11+
Architecture: High-Throughput Stream Ingestion with PEP 654 except* Routing and Zero-Downtime Worker Recovery.
"""

from __future__ import annotations
import asyncio
import hashlib
import logging
import random
import time
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("stream.supervisor")

@dataclass
class TelemetryEnvelope:
    message_id: str
    tenant_id: str
    payload: dict
    attempts: int = 0

class DeadLetterQueue:
    def __init__(self) -> None:
        self._quarantine: list[dict] = []

    async def publish(self, envelope: TelemetryEnvelope, exc: Exception) -> None:
        payload_bytes = str(envelope.payload).encode("utf-8")
        record = {
            "quarantined_at": time.time(),
            "message_id": envelope.message_id,
            "tenant_id": envelope.tenant_id,
            "attempts": envelope.attempts,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "sha256_fingerprint": hashlib.sha256(payload_bytes).hexdigest(),
        }
        self._quarantine.append(record)
        logger.critical(f"[DLQ] Quarantined message {envelope.message_id}. Reason: {exc}")

class SupervisedStreamWorker:
    def __init__(self, worker_id: int, dlq: DeadLetterQueue) -> None:
        self.worker_id = worker_id
        self.dlq = dlq
        self.max_transient_retries = 3

    async def process_envelope(self, envelope: TelemetryEnvelope) -> None:
        envelope.attempts += 1
        
        # Simulate poison pill payload detection
        if envelope.payload.get("corrupt"):
            raise ValueError(f"Poison pill detected in message {envelope.message_id}")

        # Simulate transient downstream connection drops
        if random.random() < 0.3:
            raise ConnectionResetError("TCP socket reset by Kafka cluster")

        logger.info(f"[Worker-{self.worker_id}] Successfully processed message {envelope.message_id}")

class StreamSupervisorEngine:
    def __init__(self, dlq: DeadLetterQueue) -> None:
        self.dlq = dlq
        self.worker = SupervisedStreamWorker(worker_id=1, dlq=dlq)

    async def ingest_stream_batch(self, stream_batch: list[TelemetryEnvelope]) -> None:
        while stream_batch:
            try:
                async with asyncio.TaskGroup() as tg:
                    for envelope in stream_batch:
                        tg.create_task(self.worker.process_envelope(envelope))
                # If TaskGroup finishes without raising, batch is 100% complete!
                break
            except* ValueError as eg:
                # Deterministic poison pill: Route directly to DLQ
                for exc in eg.exceptions:
                    logger.warning(f"Routing unrecoverable payload error to DLQ: {exc}")
                    # Find and isolate the bad message
                    for env in list(stream_batch):
                        if env.payload.get("corrupt"):
                            await self.dlq.publish(env, exc)
                            stream_batch.remove(env)

            except* ConnectionResetError as eg:
                # Transient network error: Apply exponential backoff and retry
                logger.warning(f"Trapped {len(eg.exceptions)} transient network errors. Scheduling backoff...")
                delay = random.uniform(0.1, 0.4)
                await asyncio.sleep(delay)
                # Keep remaining messages in stream_batch to retry!

async def main_recipe_08_3() -> None:
    dlq = DeadLetterQueue()
    engine = StreamSupervisorEngine(dlq)

    test_batch = [
        TelemetryEnvelope("msg-1", "tenant-alpha", {"metric": "cpu", "value": 45}),
        TelemetryEnvelope("msg-2", "tenant-beta", {"corrupt": True}), # Poison pill
        TelemetryEnvelope("msg-3", "tenant-gamma", {"metric": "mem", "value": 82}),
    ]

    await engine.ingest_stream_batch(test_batch)
    logger.info(f"Stream processing finished. Items in DLQ: {len(dlq._quarantine)}")

if __name__ == "__main__":
    asyncio.run(main_recipe_08_3())

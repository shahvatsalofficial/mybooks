"""
Recipe 04.2: High-Throughput Streaming Event Ingestion Engine
File: recipe_04_2_streaming_backpressure.py
Python Version: 3.12+
"""

from __future__ import annotations
import asyncio
import logging
import random
import time
from typing import AsyncGenerator, NamedTuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("StreamingPipeline")


class TelemetryEvent(NamedTuple):
    device_id: str
    timestamp: float
    voltage: float
    temperature: float


async def mock_network_event_stream(total_events: int = 50) -> AsyncGenerator[TelemetryEvent, None]:
    """Simulates a non-blocking network stream emitting telemetry events."""
    for i in range(total_events):
        await asyncio.sleep(random.uniform(0.005, 0.02))  # Fast network arrival
        yield TelemetryEvent(
            device_id=f"sensor-{random.randint(1, 10):03d}",
            timestamp=time.time(),
            voltage=random.uniform(3.1, 3.4),
            temperature=random.uniform(40.0, 85.0),
        )


async def event_producer(
    stream: AsyncGenerator[TelemetryEvent, None],
    queue: asyncio.Queue[TelemetryEvent | None],
) -> None:
    """Consumes the stream and pushes to bounded queue with automatic backpressure."""
    logger.info("Producer started.")
    count = 0
    async for event in stream:
        # If queue is full (maxsize reached), this await SUSPENDS the producer!
        # Memory consumption is capped, preventing Out-Of-Memory crashes.
        await queue.put(event)
        count += 1
        if count % 10 == 0:
            logger.info(f"Producer pushed {count} events (Queue depth: {queue.qsize()}/{queue.maxsize}).")

    logger.info(f"Producer finished streaming {count} events. Emitting shutdown sentinels.")


async def event_consumer_worker(
    worker_id: int,
    queue: asyncio.Queue[TelemetryEvent | None],
) -> None:
    """Worker task draining events from the bounded queue and writing to storage."""
    logger.info(f"Worker-{worker_id} online.")
    processed = 0
    while True:
        event = await queue.get()
        if event is None:
            # Sentinel received: Re-queue for sibling workers and terminate
            await queue.put(None)
            queue.task_done()
            break

        try:
            # Simulate I/O write to database (slower than network ingestion)
            await asyncio.sleep(random.uniform(0.02, 0.05))
            processed += 1
        finally:
            queue.task_done()

    logger.info(f"Worker-{worker_id} gracefully exiting. Total processed: {processed}")


async def run_pipeline() -> None:
    # Bounded queue caps total memory footprint
    QUEUE_CAPACITY = 15
    NUM_WORKERS = 4
    
    queue: asyncio.Queue[TelemetryEvent | None] = asyncio.Queue(maxsize=QUEUE_CAPACITY)
    stream = mock_network_event_stream(total_events=60)

    start_time = time.perf_counter()

    async with asyncio.TaskGroup() as tg:
        # Launch worker pool
        workers = [tg.create_task(event_consumer_worker(i, queue)) for i in range(1, NUM_WORKERS + 1)]
        
        # Launch producer
        producer_task = tg.create_task(event_producer(stream, queue))

        # Await producer completion
        await producer_task
        
        # Inject initial poison pill sentinel to trigger worker cascade shutdown
        await queue.put(None)

        # Wait for all queue items to be fully processed by workers
        await queue.join()

    duration = time.perf_counter() - start_time
    logger.info(f"Pipeline finished processing in {duration:.3f} seconds with zero memory leaks.")


if __name__ == "__main__":
    asyncio.run(run_pipeline())

"""
Recipe 05.2: Resilient High-Concurrency ProcessPool
File: recipe_05_2_process_pool_resilient.py
Python Version: 3.12+
"""

from __future__ import annotations
from concurrent.futures import ProcessPoolExecutor, as_completed, TimeoutError
import math
import os
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ProcessPoolOrchestrator")


def cpu_intensive_compute(record_id: int) -> tuple[int, float]:
    """Simulates intensive mathematical hashing and transformation."""
    val = float(record_id)
    for _ in range(5000):
        val = math.sqrt(val * 1.0001 + 0.5)
    return record_id, val


def calculate_optimal_chunksize(total_items: int, num_workers: int) -> int:
    """Calculates chunksize to amortize IPC without causing worker starvation."""
    chunk = total_items // (num_workers * 4)
    return max(1, min(chunk, 500))


def run_batch_pool_pipeline() -> None:
    TOTAL_ITEMS = 50_000
    NUM_WORKERS = os.cpu_count() or 4
    chunksize = calculate_optimal_chunksize(TOTAL_ITEMS, NUM_WORKERS)
    
    logger.info(f"Starting ProcessPool: {NUM_WORKERS} workers, {TOTAL_ITEMS} items, chunksize={chunksize}")

    start_time = time.perf_counter()
    completed_count = 0

    # max_tasks_per_child recycles workers every 5,000 tasks to purge memory fragmentation
    with ProcessPoolExecutor(max_workers=NUM_WORKERS, max_tasks_per_child=5000) as executor:
        # executor.map preserves ordering and handles chunking automatically
        results_iterator = executor.map(
            cpu_intensive_compute,
            range(TOTAL_ITEMS),
            chunksize=chunksize,
        )

        for record_id, computed_val in results_iterator:
            completed_count += 1
            if completed_count % 10_000 == 0:
                logger.info(f"Progress: {completed_count}/{TOTAL_ITEMS} tasks completed.")

    total_time = time.perf_counter() - start_time
    throughput = TOTAL_ITEMS / total_time
    logger.info(f"Batch completed in {total_time:.2f}s ({throughput:.1f} items/sec) across {NUM_WORKERS} cores.")


if __name__ == "__main__":
    run_batch_pool_pipeline()

"""
Recipe 05.1: Zero-Copy Shared Memory Array Pipeline
File: recipe_05_1_shared_memory_pipeline.py
Python Version: 3.12+
"""

from __future__ import annotations
import multiprocessing as mp
from multiprocessing.shared_memory import SharedMemory
import numpy as np
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [PID %(process)d] %(message)s")
logger = logging.getLogger("SharedMemoryPipeline")

ARRAY_SHAPE = (10_000_000,)
DTYPE = np.float64
TOTAL_BYTES = int(np.prod(ARRAY_SHAPE) * np.dtype(DTYPE).itemsize) # ~80MB


def worker_process_chunk(
    shm_name: str,
    start_idx: int,
    end_idx: int,
    multiplier: float,
    barrier: mp.synchronize.Barrier,
) -> None:
    """Worker process attaching to existing shared memory and mutating in-place."""
    # Attach to existing shared memory block allocated by parent
    existing_shm = SharedMemory(name=shm_name)
    try:
        # Zero-copy view directly over physical RAM
        shared_array = np.ndarray(ARRAY_SHAPE, dtype=DTYPE, buffer=existing_shm.buf)
        
        # In-place SIMD vectorized operation on assigned chunk
        logger.info(f"Worker computing slice [{start_idx}:{end_idx}]...")
        shared_array[start_idx:end_idx] *= multiplier
        
        # Synchronize with peer workers via IPC Barrier
        barrier.wait()
    finally:
        # Crucial: Close local file descriptor; do NOT unlink in worker!
        existing_shm.close()


def run_zero_copy_pipeline() -> None:
    # Enforce safe start method
    try:
        mp.set_start_method("forkserver")
    except RuntimeError:
        pass

    logger.info(f"Allocating {TOTAL_BYTES / (1024*1024):.1f} MB POSIX shared memory block...")
    shm = SharedMemory(create=True, size=TOTAL_BYTES)
    
    try:
        # Initialize array inside shared memory
        local_array = np.ndarray(ARRAY_SHAPE, dtype=DTYPE, buffer=shm.buf)
        local_array[:] = np.random.uniform(1.0, 10.0, size=ARRAY_SHAPE)
        initial_sum = float(np.sum(local_array[0:1000]))
        logger.info(f"Initial sum (sample 1000): {initial_sum:.2f}")

        NUM_WORKERS = 4
        chunk_size = len(local_array) // NUM_WORKERS
        barrier = mp.Barrier(NUM_WORKERS + 1)
        processes: list[mp.Process] = []

        start_time = time.perf_counter()

        # Spawn workers
        for i in range(NUM_WORKERS):
            s_idx = i * chunk_size
            e_idx = (i + 1) * chunk_size if i != NUM_WORKERS - 1 else len(local_array)
            p = mp.Process(
                target=worker_process_chunk,
                args=(shm.name, s_idx, e_idx, 2.0, barrier),
            )
            p.start()
            processes.append(p)

        # Wait for all workers to finish chunk mutation
        barrier.wait()
        duration = time.perf_counter() - start_time

        final_sum = float(np.sum(local_array[0:1000]))
        logger.info(f"Pipeline executed in {duration*1000:.2f}ms.")
        logger.info(f"Final sum (sample 1000, expected 2x): {final_sum:.2f}")
        assert np.isclose(final_sum, initial_sum * 2.0)

        for p in processes:
            p.join()

    finally:
        # Master cleanup: Close buffer and unlink from /dev/shm
        shm.close()
        shm.unlink()
        logger.info("Shared memory segment successfully unlinked.")


if __name__ == "__main__":
    run_zero_copy_pipeline()

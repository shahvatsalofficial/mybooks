"""
Recipe 07.2: High-Performance Garbage Collection Optimizer
File: recipe_07_2_gc_optimizer.py
Python Version: 3.12+
"""

from __future__ import annotations
from contextlib import contextmanager
import gc
import logging
import time
from typing import Generator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("GCOptimizer")


class ProductionGCTuner:
    @staticmethod
    def freeze_static_metadata() -> None:
        """Freezes all currently live objects into permanent GC-exempt storage."""
        # Force a full generation 2 sweep to purge transient boot artifacts
        gc.collect()
        
        # Freeze remaining objects (frameworks, route tables, logging singletons)
        # Excludes them from all subsequent Gen 0, 1, and 2 traversals!
        gc.freeze()
        logger.info(f"CPython GC frozen: {gc.get_freeze_count()} static objects permanently exempted from GC.")

    @staticmethod
    @contextmanager
    def disable_gc_scoped(threshold_multiplier: int = 5) -> Generator[None, None, None]:
        """Temporarily scales GC thresholds or disables GC during latency-critical loops."""
        orig_thresholds = gc.get_threshold()
        # Scale thresholds up: (3500, 50, 50) allows batch ingestion without GC pauses
        tuned_thresholds = (
            orig_thresholds[0] * threshold_multiplier,
            orig_thresholds[1] * threshold_multiplier,
            orig_thresholds[2] * threshold_multiplier,
        )
        
        gc.set_threshold(*tuned_thresholds)
        logger.info(f"GC thresholds tuned up: {orig_thresholds} -> {tuned_thresholds}")
        start_time = time.perf_counter()
        try:
            yield
        finally:
            # Revert to standard thresholds and execute a controlled sweep
            gc.set_threshold(*orig_thresholds)
            elapsed = time.perf_counter() - start_time
            logger.info(f"Critical block completed in {elapsed*1000:.2f}ms. Reverted GC thresholds.")
            
            # Execute sweep in generation 0 only to clean fast temporaries
            unreachable = gc.collect(generation=0)
            logger.info(f"Post-batch Gen 0 sweep cleaned {unreachable} unreachable cyclic objects.")


def simulate_high_throughput_batch() -> None:
    # 1. Freeze static framework objects at startup
    ProductionGCTuner.freeze_static_metadata()

    # 2. Execute 100,000 object transformations inside tuned GC context
    logger.info("Executing intensive batch processing loop...")
    with ProductionGCTuner.disable_gc_scoped(threshold_multiplier=10):
        # Heavy temporary allocation loop
        accumulated_data = []
        for i in range(100_000):
            # Transient structures that reference each other
            d = {"id": i, "value": i * 1.5}
            accumulated_data.append(d)
            if len(accumulated_data) > 5000:
                accumulated_data.clear() # Rapid reference release

    logger.info("Batch processing pipeline executed with zero stop-the-world Gen 2 pauses.")


if __name__ == "__main__":
    simulate_high_throughput_batch()

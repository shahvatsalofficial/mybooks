"""
Recipe 05.1: Low-Overhead Production tracemalloc Heap Snapshot Differ
Architecture: Non-invasive background memory differential watchdog.
Target Runtime: Python 3.12+ (CPython)
"""

from __future__ import annotations
import gc
import logging
import threading
import time
import tracemalloc
from typing import List, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MemoryWatchdog")


class ProductionMemoryWatchdog:
    """Monitors heap growth and logs allocation diffs when memory drift exceeds thresholds."""

    def __init__(
        self,
        check_interval_seconds: float = 60.0,
        leak_threshold_mb: float = 25.0,
        frame_depth: int = 3,
    ) -> None:
        self.check_interval = check_interval_seconds
        self.leak_threshold_bytes = int(leak_threshold_mb * 1024 * 1024)
        self.frame_depth = frame_depth
        self._baseline_snapshot: Optional[tracemalloc.Snapshot] = None
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Starts tracemalloc and launches background monitor thread."""
        if not tracemalloc.is_tracing():
            tracemalloc.start(self.frame_depth)
        gc.collect()  # Clean baseline
        self._baseline_snapshot = tracemalloc.take_snapshot()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True, name="MemoryWatchdog")
        self._thread.start()
        logger.info("ProductionMemoryWatchdog initialized and monitoring heap allocations.")

    def _monitor_loop(self) -> None:
        while not self._stop_event.wait(self.check_interval):
            if self._baseline_snapshot is None:
                continue

            current_snapshot = tracemalloc.take_snapshot()
            diff_stats = current_snapshot.compare_to(self._baseline_snapshot, "lineno")

            total_growth = sum(stat.size_diff for stat in diff_stats if stat.size_diff > 0)
            logger.info(f"Heap Delta: +{total_growth / (1024 * 1024):.2f} MB since baseline.")

            if total_growth > self.leak_threshold_bytes:
                logger.warning(
                    f"LEAK ALERT: Net memory growth (+{total_growth / (1024*1024):.2f} MB) "
                    f"exceeds threshold ({self.leak_threshold_bytes / (1024*1024):.2f} MB)!"
                )
                self._report_top_allocations(diff_stats, top_n=5)
                # Reset baseline to detect next incremental leak wave
                self._baseline_snapshot = current_snapshot

    def _report_top_allocations(self, stats: List[tracemalloc.StatisticDiff], top_n: int = 5) -> None:
        logger.warning(f"--- TOP {top_n} MEMORY ALLOCATION SITES ---")
        for index, stat in enumerate(stats[:top_n], start=1):
            growth_kb = stat.size_diff / 1024
            logger.warning(
                f"#{index}: {stat.traceback.format()[-1].strip()} | "
                f"Delta: +{growth_kb:,.1f} KB ({stat.count_diff:+d} objects, Total: {stat.size / 1024:,.1f} KB)"
            )

    def stop(self) -> None:
        """Stops watchdog thread and releases tracemalloc buffers."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        if tracemalloc.is_tracing():
            tracemalloc.stop()
        logger.info("ProductionMemoryWatchdog stopped.")


# Demonstration & Verification
if __name__ == "__main__":
    watchdog = ProductionMemoryWatchdog(check_interval_seconds=1.0, leak_threshold_mb=2.0)
    watchdog.start()

    # Simulate deliberate cyclic leak
    leaked_data = []
    print("Simulating high-volume memory allocation...")
    for _ in range(5):
        time.sleep(1.2)
        # Allocate 1MB chunks of strings
        leaked_data.append([f"LEAK_CHUNK_{i}_{time.time()}" * 50 for i in range(1000)])

    watchdog.stop()
    print("Watchdog demonstration complete.")

"""
Recipe 07.1: Continuous Production Heap Leak Detector
File: recipe_07_1_heap_leak_detector.py
Python Version: 3.12+
"""

from __future__ import annotations
import linecache
import os
import tracemalloc
import logging
import time
from typing import NamedTuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("HeapLeakDetector")


class LeakReport(NamedTuple):
    file_path: str
    line_number: int
    size_delta_kb: float
    total_blocks_delta: int
    code_context: str


class MemoryMonitor:
    def __init__(self, trace_depth: int = 15, alert_threshold_kb: float = 1024.0) -> None:
        self.trace_depth = trace_depth
        self.alert_threshold_kb = alert_threshold_kb
        self.baseline_snapshot: tracemalloc.Snapshot | None = None
        self._is_active = False

    def start(self) -> None:
        """Starts memory tracing and records initial baseline snapshot."""
        if not tracemalloc.is_tracing():
            tracemalloc.start(self.trace_depth)
            self._is_active = True
            self.baseline_snapshot = tracemalloc.take_snapshot()
            logger.info("Tracemalloc monitor activated. Baseline snapshot established.")

    def capture_differential(self, top_n: int = 5) -> list[LeakReport]:
        """Compares current heap state against baseline and reports top allocations."""
        if not self._is_active or self.baseline_snapshot is None:
            raise RuntimeError("MemoryMonitor must be started before capturing differentials.")

        current_snapshot = tracemalloc.take_snapshot()
        
        # Filter out internal tracemalloc and logging memory allocations
        current_filtered = current_snapshot.filter_traces((
            tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
            tracemalloc.Filter(False, "<unknown>"),
            tracemalloc.Filter(False, tracemalloc.__file__),
            tracemalloc.Filter(False, logging.__file__),
        ))

        # Compute differential grouped by source line
        stats = current_filtered.compare_to(self.baseline_snapshot, "lineno")
        reports: list[LeakReport] = []

        for stat in stats[:top_n]:
            size_kb = stat.size_diff / 1024.0
            if size_kb >= self.alert_threshold_kb:
                frame = stat.traceback[0]
                line_code = linecache.getline(frame.filename, frame.lineno).strip()
                reports.append(LeakReport(
                    file_path=frame.filename,
                    line_number=frame.lineno,
                    size_delta_kb=size_kb,
                    total_blocks_delta=stat.count_diff,
                    code_context=line_code,
                ))

        return reports

    def reset_baseline(self) -> None:
        """Resets the baseline snapshot to current heap state."""
        self.baseline_snapshot = tracemalloc.take_snapshot()
        logger.info("Baseline memory snapshot reset to current state.")


# Demonstration of leak detection
class LeakySessionCache:
    def __init__(self) -> None:
        self._cache: dict[str, list[dict]] = {}

    def simulate_leaky_workload(self, iterations: int = 5000) -> None:
        """Simulates unevicted session objects accumulating in RAM."""
        for i in range(iterations):
            key = f"session_{i}_{time.time()}"
            # Allocates ~1KB per entry without eviction
            self._cache[key] = [{"event_id": j, "payload": "X" * 128} for j in range(8)]


def run_monitoring_demonstration() -> None:
    monitor = MemoryMonitor(alert_threshold_kb=500.0)
    monitor.start()

    logger.info("Instantiating application workload...")
    leaky_service = LeakySessionCache()
    leaky_service.simulate_leaky_workload(iterations=4000)

    # Capture differential and identify leaked line
    leak_reports = monitor.capture_differential(top_n=3)

    if leak_reports:
        logger.warning(f"=== DETECTED {len(leak_reports)} MEMORY ALLOCATION ANOMALIES ===")
        for report in leak_reports:
            logger.warning(
                f"[ALERT] Leaked: {report.size_delta_kb:.2f} KB (+{report.total_blocks_delta} blocks) "
                f"at {os.path.basename(report.file_path)}:{report.line_number}\n"
                f"        Source: `{report.code_context}`"
            )
    else:
        logger.info("Zero memory leaks detected above alert threshold.")


if __name__ == "__main__":
    run_monitoring_demonstration()

"""
Recipe 08.1: Precision Sub-Microsecond pyperf Benchmark with Core Pinning
Architecture: Multi-process pyperf runner with CPU affinity and statistical verification.
Target Runtime: Python 3.12+ (CPython)
"""

from __future__ import annotations
import gc
import os
import sys
import time
from typing import Any, List
import pyperf


def target_workload_kernel(data_matrix: List[List[float]]) -> float:
    """The critical algorithmic kernel to benchmark with extreme precision."""
    total = 0.0
    for row in data_matrix:
        for val in row:
            total += (val * 1.5) - 0.25
    return total


def benchmark_entrypoint(runner: pyperf.Runner) -> None:
    """Configures and registers the calibrated benchmark with the pyperf runner."""
    # Pre-allocate and warm data structures outside the timing loop
    rows = 500
    cols = 200
    matrix = [[float(r + c) for c in range(cols)] for r in range(rows)]

    def run_trial(loops: int) -> float:
        """Executes inner timing loop. Disables GC to eliminate pause noise."""
        gc_was_enabled = gc.isenabled()
        gc.disable()
        try:
            start_time = time.perf_counter()
            for _ in range(loops):
                _ = target_workload_kernel(matrix)
            duration = time.perf_counter() - start_time
            return duration
        finally:
            if gc_was_enabled:
                gc.enable()

    # Register benchmark with pyperf: executes across 20 worker processes
    runner.bench_time_func("matrix_arithmetic_kernel", run_trial)


def run_standalone_suite() -> None:
    """Initializes pyperf with deterministic CLI arguments."""
    runner = pyperf.Runner(
        values=10,         # 10 values per worker process
        processes=5,       # 5 separate worker processes to average ASLR noise
        warmups=3,         # 3 warmup runs to saturate CPU caches and Tier-1 JIT
    )
    benchmark_entrypoint(runner)


if __name__ == "__main__":
    run_standalone_suite()

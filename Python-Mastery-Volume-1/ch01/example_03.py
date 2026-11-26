"""
Recipe 01.2: GIL Contention Analyzer & Thread Switch Telemetry Engine
File: recipe_01_2_gil_contention_analyzer.py
Python Version: 3.12+
"""

from __future__ import annotations
import sys
import time
import threading
import statistics
from dataclasses import dataclass, field
from typing import List


@dataclass
class ThreadTelemetry:
    thread_name: str
    iterations: int = 0
    total_wait_ns: int = 0
    max_wait_ns: int = 0
    samples_ns: List[int] = field(default_factory=list)


class GILContentionTelemetryEngine:
    """Monitors and profiles Global Interpreter Lock handover latencies in multi-threaded runtimes."""

    def __init__(self, switch_interval_sec: float = 0.005) -> None:
        self.switch_interval_sec = switch_interval_sec
        self.original_interval = sys.getswitchinterval()
        self._stop_event = threading.Event()
        self.metrics: dict[str, ThreadTelemetry] = {}

    def __enter__(self) -> GILContentionTelemetryEngine:
        sys.setswitchinterval(self.switch_interval_sec)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        sys.setswitchinterval(self.original_interval)

    def _io_worker(self, name: str, iterations: int) -> None:
        """Simulates latency-sensitive I/O polling with GIL release cycles."""
        telemetry = ThreadTelemetry(thread_name=name)
        self.metrics[name] = telemetry

        for _ in range(iterations):
            if self._stop_event.is_set():
                break

            # Measure GIL re-acquisition latency after simulated I/O sleep
            time.sleep(0.001)  # Releases GIL during sleep
            start = time.perf_counter_ns()
            
            # This bytecode instruction forces GIL acquisition
            _ = sys.flags
            
            acquire_elapsed_ns = time.perf_counter_ns() - start
            telemetry.iterations += 1
            telemetry.total_wait_ns += acquire_elapsed_ns
            telemetry.samples_ns.append(acquire_elapsed_ns)
            if acquire_elapsed_ns > telemetry.max_wait_ns:
                telemetry.max_wait_ns = acquire_elapsed_ns

    def _cpu_worker(self, name: str, iterations: int) -> None:
        """Simulates a heavy computational workload holding the GIL."""
        telemetry = ThreadTelemetry(thread_name=name)
        self.metrics[name] = telemetry

        val = 0
        for i in range(iterations):
            if self._stop_event.is_set():
                break
            val = (val + i) ^ (i & 0xFF)
            telemetry.iterations += 1

    def run_benchmark(self, io_threads: int = 2, cpu_threads: int = 2, duration_sec: float = 3.0) -> None:
        """Executes a controlled concurrent execution benchmark."""
        print(f"[*] Initializing GIL Contention Audit: {cpu_threads} CPU Threads, {io_threads} I/O Threads")
        print(f"[*] CPython switch interval configured to: {self.switch_interval_sec * 1000:.2f} ms")

        workers: List[threading.Thread] = []

        for i in range(cpu_threads):
            t = threading.Thread(
                target=self._cpu_worker,
                args=(f"CPU-Worker-{i+1}", 20_000_000),
                daemon=True,
            )
            workers.append(t)

        for i in range(io_threads):
            t = threading.Thread(
                target=self._io_worker,
                args=(f"IO-Worker-{i+1}", 1_000),
                daemon=True,
            )
            workers.append(t)

        start_time = time.time()
        for t in workers:
            t.start()

        time.sleep(duration_sec)
        self._stop_event.set()

        for t in workers:
            t.join(timeout=1.0)

        elapsed = time.time() - start_time
        self._render_report(elapsed)

    def _render_report(self, elapsed_sec: float) -> None:
        """Renders statistical analysis of thread latency distributions."""
        divider = "=" * 80
        print("\n" + divider)
        print(f"GIL CONTENTION & CONVOY TELEMETRY REPORT (Total Time: {elapsed_sec:.2f}s)")
        print(divider)
        print(f"{'THREAD NAME':<18} {'OPS COMPLETED':<14} {'AVG WAIT (µs)':<14} {'P99 WAIT (µs)':<14} {'MAX WAIT (µs)'}")
        print("-" * 80)

        for name, data in self.metrics.items():
            if not data.samples_ns:
                print(f"{name:<18} {data.iterations:<14} {'N/A (CPU-Bound)':<14} {'N/A':<14} {'N/A'}")
                continue

            samples_us = [s / 1000.0 for s in data.samples_ns]
            avg_us = statistics.mean(samples_us)
            p99_us = statistics.quantiles(samples_us, n=100)[98] if len(samples_us) >= 100 else max(samples_us)
            max_us = data.max_wait_ns / 1000.0

            print(f"{name:<18} {data.iterations:<14} {avg_us:<14.2f} {p99_us:<14.2f} {max_us:<14.2f}")

        print(divider)
        print("[!] Systems Recommendation: If I/O P99 exceeds 5000µs (5ms), refactor CPU workers")
        print("    to concurrent.futures.ProcessPoolExecutor or native PyO3 Rust extensions.")
        print(divider + "\n")


if __name__ == "__main__":
    with GILContentionTelemetryEngine(switch_interval_sec=0.005) as engine:
        engine.run_benchmark(io_threads=2, cpu_threads=2, duration_sec=2.0)

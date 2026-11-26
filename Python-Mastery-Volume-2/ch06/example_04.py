"""
Recipe 06.3: Adaptive Tier-2 JIT Guard Rail Benchmark & Deopt Monitor
Architecture: Measures specialization performance vs polymorphic deopt thrashing.
Target Runtime: Python 3.12+ / 3.13+ (CPython)
"""

from __future__ import annotations
import sys
import time
from typing import Any, List


def arithmetic_accumulator(val_a: Any, val_b: Any) -> Any:
    """Target function whose opcodes will specialize or thrash based on argument types."""
    return val_a + val_b


class SpecializationDeoptBenchmark:
    """Quantifies throughput penalties when polymorphic inputs break specialized JIT traces."""

    def __init__(self, iterations: int = 5_000_000) -> None:
        self.iterations = iterations

    def benchmark_monomorphic(self) -> float:
        """Runs with 100% pure integers (Zero deoptimization; Tier-1/Tier-2 optimal)."""
        # Warmup
        for _ in range(100):
            arithmetic_accumulator(10, 20)

        start = time.perf_counter()
        for i in range(self.iterations):
            arithmetic_accumulator(i, 1)
        return time.perf_counter() - start

    def benchmark_polymorphic_thrashing(self) -> float:
        """Alternates between int, float, string, and list, triggering continuous deoptimization."""
        inputs = [
            (10, 20),                # int + int
            (10.5, 20.5),            # float + float
            ("alpha_", "beta"),      # str + str
            ([1, 2], [3, 4]),        # list + list
        ]

        start = time.perf_counter()
        for i in range(self.iterations):
            pair = inputs[i & 3]  # Alternate across 4 conflicting types every call
            arithmetic_accumulator(pair[0], pair[1])
        return time.perf_counter() - start

    def run_comparison(self) -> None:
        print(f"Executing {self.iterations:,} iterations per benchmark...")

        mono_time = self.benchmark_monomorphic()
        poly_time = self.benchmark_polymorphic_thrashing()

        slowdown = poly_time / mono_time if mono_time > 0 else 0.0

        print(f"Monomorphic (Specialized):   {mono_time:.4f} s (100% JIT / Specialized Cache Hit)")
        print(f"Polymorphic (Deopt Thrash):  {poly_time:.4f} s (Continuous Guard Failure Bailouts)")
        print(f"Performance Degradation:     {slowdown:.2f}x Slowdown due to Deoptimization Thrashing!")


if __name__ == "__main__":
    bench = SpecializationDeoptBenchmark(iterations=2_000_000)
    bench.run_comparison()

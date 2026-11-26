"""
Setup build script (setup.py) and invocation interface for Recipe 06.2
Compile via: python setup.py build_ext --inplace
"""

from __future__ import annotations
import time
import numpy as np


def run_cython_benchmark() -> None:
    try:
        from fast_kernel import fast_exponential_moving_average  # type: ignore[import-not-found]
    except ImportError:
        print("Note: Compile Cython module first via: python setup.py build_ext --inplace")
        return

    sample_size = 10_000_000
    print(f"Allocating {sample_size:,} contiguous float64 elements...")
    prices = np.random.normal(150.0, 5.0, sample_size).astype(np.float64)
    output_cython = np.empty(sample_size, dtype=np.float64)

    start = time.perf_counter()
    # Direct typed memoryview execution: 0 Python boxing overhead!
    fast_exponential_moving_average(prices, 0.05, output_cython)
    duration = time.perf_counter() - start

    rate = sample_size / duration
    print(f"Cython EMA processed {sample_size:,} items in {duration:.4f} s ({rate:,.0f} ticks/sec)")
    print(f"First 5 EMA Results: {output_cython[:5]}")


if __name__ == "__main__":
    run_cython_benchmark()

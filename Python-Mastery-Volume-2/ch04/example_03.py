"""
Python Client Interface for Recipe 04.2
Compiles with maturin (maturin develop --release)
"""

from __future__ import annotations
import random
import time


def demonstrate_rust_bridge() -> None:
    try:
        import fast_numerical_engine  # type: ignore[import-not-found]
    except ImportError:
        print("Note: Run 'maturin develop --release' to compile the Rust extension.")
        return

    # Generate 5,000,000 float samples
    dataset = [random.gauss(100.0, 15.0) for _ in range(5_000_000)]
    print(f"Generated {len(dataset):,} random samples. Invoking Rust parallel filter...")

    start_time = time.perf_counter()
    # GIL is automatically released in Rust during computation!
    anomalies = fast_numerical_engine.parallel_variance_filter(dataset, 3.0)
    duration = time.perf_counter() - start_time

    print(f"Identified {len(anomalies):,} anomalies (>3-sigma) in {duration:.3f} s.")


if __name__ == "__main__":
    demonstrate_rust_bridge()

import time
import functools
from typing import Callable, TypeVar, ParamSpec

P = ParamSpec('P')
R = TypeVar('R')

def audit_latency(func: Callable[P, R]) -> Callable[P, R]:
    """Production latency auditing decorator preserving exact type signatures."""
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.perf_counter_ns()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed_us = (time.perf_counter_ns() - start) / 1000.0
            print(f"[METRIC] {func.__name__} executed in {elapsed_us:.2f}µs")
    return wrapper

@audit_latency
def process_order(order_id: int, symbol: str, quantity: int = 100) -> bool:
    return True

# IDE autocompletion and Mypy strictly enforce:
# process_order(order_id=101, symbol="NVDA", quantity=50) -> bool
# Passing process_order("invalid", symbol=42) triggers compile-time rejection!

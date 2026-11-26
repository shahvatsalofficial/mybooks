"""
Recipe 01.3: Adaptive Tier-1 Inline Cache Profiler & Quickened Bytecode Validator
File: recipe_01_3_specialization_profiler.py
Python Version: 3.12+
"""

from __future__ import annotations
import dis
import sys
import time
from typing import Any, Callable, Dict, List


class SpecializationAuditEngine:
    """Audits whether CPython 3.12+ functions have achieved opcode specialization."""

    @staticmethod
    def get_opcode_distribution(func: Callable[..., Any]) -> Dict[str, int]:
        """Extracts current opcode frequencies directly from active bytecode."""
        distribution: Dict[str, int] = {}
        for instr in dis.Bytecode(func, show_caches=True):
            distribution[instr.opname] = distribution.get(instr.opname, 0) + 1
        return distribution

    @classmethod
    def audit_loop_specialization(
        cls,
        target_function: Callable[..., Any],
        sample_args_generator: Callable[[], tuple[Any, ...]],
        warmup_iterations: int = 100,
    ) -> None:
        """Executes a target function through cold, warm, and specialized cycles."""
        print(f"[*] Auditing PEP 659 Specialization State for: {target_function.__name__}()")

        # Capture Cold State
        cold_dist = cls.get_opcode_distribution(target_function)

        # Warmup loop to trigger adaptive quickening (PEP 659 threshold = 8 iterations)
        start_time = time.perf_counter()
        for _ in range(warmup_iterations):
            args = sample_args_generator()
            target_function(*args)
        elapsed = time.perf_counter() - start_time

        # Capture Specialized State
        warm_dist = cls.get_opcode_distribution(target_function)

        # Analysis
        specialized_ops = [
            op for op in warm_dist if any(
                suffix in op for suffix in [
                    "_MODULE", "_INSTANCE_VALUE", "_ADD_INT", "_LIST_INT", "_EXACT_ARGS"
                ]
            )
        ]

        divider = "=" * 80
        print("\n" + divider)
        print(f"PEP 659 SPECIALIZATION AUDIT REPORT: {target_function.__name__}")
        print(f"Warmup Completed: {warmup_iterations:,} executions in {elapsed*1000:.2f} ms")
        print(divider)
        print(f"{'OPCODE':<35} {'COLD COUNT':<15} {'WARM COUNT':<15} {'STATUS'}")
        print("-" * 80)

        all_ops = sorted(set(list(cold_dist.keys()) + list(warm_dist.keys())))
        for op in all_ops:
            if op == "CACHE":
                continue
            c_cnt = cold_dist.get(op, 0)
            w_cnt = warm_dist.get(op, 0)

            status = "Unchanged"
            if any(suffix in op for suffix in ["_MODULE", "_INSTANCE_VALUE", "_ADD_INT", "_LIST_INT"]):
                status = "SPECIALIZED (Optimized)"
            elif c_cnt > 0 and w_cnt == 0:
                status = "Specialized Away"

            print(f"{op:<35} {c_cnt:<15} {w_cnt:<15} {status}")

        print(divider)
        if specialized_ops:
            print(f"[SUCCESS] Function successfully specialized {len(specialized_ops)} opcodes:")
            for s_op in specialized_ops:
                print(f"  + {s_op} is active in inline cache")
        else:
            print("[WARNING] Function failed to specialize. Check for polymorphic types or global churn.")
        print(divider + "\n")


# Domain Model for Verification
class TradeOrder:
    __slots__ = ("order_id", "symbol", "quantity", "price")

    def __init__(self, order_id: int, symbol: str, quantity: int, price: float) -> None:
        self.order_id = order_id
        self.symbol = symbol
        self.quantity = quantity
        self.price = price


def calculate_portfolio_exposure(orders: List[TradeOrder]) -> float:
    """Target function to verify attribute and arithmetic specialization."""
    total_exposure = 0.0
    for order in orders:
        total_exposure = total_exposure + (order.quantity * order.price)
    return total_exposure


if __name__ == "__main__":
    test_batch = [
        TradeOrder(i, "AAPL", 100 + i, 185.50) for i in range(50)
    ]

    SpecializationAuditEngine.audit_loop_specialization(
        target_function=calculate_portfolio_exposure,
        sample_args_generator=lambda: (test_batch,),
        warmup_iterations=500,
    )

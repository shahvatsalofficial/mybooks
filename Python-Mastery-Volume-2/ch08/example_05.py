"""
Recipe 08.3: Automated Flamegraph Regression CI Pipeline with Latency Gates
Architecture: Statistical regression gating pipeline executing Mann-Whitney U tests.
Target Runtime: Python 3.12+ (CPython / CI Runner)
"""

from __future__ import annotations
import json
import math
import sys
from typing import Any, Dict, List, Tuple


def calculate_mann_whitney_u(baseline: List[float], candidate: List[float]) -> Tuple[float, float]:
    """Computes the Mann-Whitney U statistic and asymptotic p-value."""
    n1 = len(baseline)
    n2 = len(candidate)
    if n1 == 0 or n2 == 0:
        raise ValueError("Sample sets cannot be empty")

    # Combine and sort all samples with provenance tags
    combined: List[Tuple[float, int]] = [(x, 1) for x in baseline] + [(y, 2) for y in candidate]
    combined.sort(key=lambda item: item[0])

    # Assign ranks (handling ties via mid-ranks)
    ranks_sum_1 = 0.0
    i = 0
    while i < len(combined):
        j = i
        while j < len(combined) - 1 and combined[j][0] == combined[j + 1][0]:
            j += 1
        avg_rank = (i + 1 + j + 1) / 2.0
        for k in range(i, j + 1):
            if combined[k][1] == 1:
                ranks_sum_1 += avg_rank
        i = j + 1

    u1 = (n1 * n2) + (n1 * (n1 + 1) / 2.0) - ranks_sum_1
    u2 = (n1 * n2) - u1
    u = min(u1, u2)

    # Compute normal approximation
    mean_u = (n1 * n2) / 2.0
    sigma_u = math.sqrt((n1 * n2 * (n1 + n2 + 1)) / 12.0)
    z = (u - mean_u) / sigma_u if sigma_u > 0 else 0.0

    # Two-tailed p-value approximation via complementary error function
    p_value = math.erfc(abs(z) / math.sqrt(2.0))
    return u, p_value


class CIRegressionGate:
    """Evaluates pull request performance metrics against baseline golden data."""

    def __init__(self, max_allowed_regression_pct: float = 2.0, alpha: float = 0.01) -> None:
        self.max_allowed_pct = max_allowed_regression_pct
        self.alpha = alpha

    def evaluate_gate(self, baseline_samples: List[float], candidate_samples: List[float]) -> bool:
        """Evaluates whether the candidate regression breaches the statistical CI gate."""
        median_base = sorted(baseline_samples)[len(baseline_samples) // 2]
        median_cand = sorted(candidate_samples)[len(candidate_samples) // 2]

        pct_change = ((median_cand - median_base) / median_base) * 100.0
        u_stat, p_val = calculate_mann_whitney_u(baseline_samples, candidate_samples)

        print("=== CI PERFORMANCE REGRESSION AUDIT ===")
        print(f"Baseline Median:   {median_base * 1000:.3f} ms (N={len(baseline_samples)})")
        print(f"Candidate Median:  {median_cand * 1000:.3f} ms (N={len(candidate_samples)})")
        print(f"Latency Delta:     {pct_change:+.2f}%")
        print(f"Mann-Whitney U:    {u_stat:.1f} (p-value = {p_val:.6f})")

        # Determine regression gate verdict
        if pct_change > self.max_allowed_pct and p_val < self.alpha:
            print(f"\n❌ CI GATE FAILED: Statistically significant regression (+{pct_change:.2f}% > {self.max_allowed_pct}%)!")
            print("Action: Pull request blocked. Inspect flamegraph profile diffs.")
            return False

        if pct_change < -self.max_allowed_pct and p_val < self.alpha:
            print(f"\n✅ CI GATE PASSED: Statistically significant performance IMPROVEMENT ({pct_change:.2f}%)!")
            return True

        print(f"\n✅ CI GATE PASSED: Latency delta ({pct_change:+.2f}%) within acceptable tolerance limits.")
        return True


if __name__ == "__main__":
    gate = CIRegressionGate(max_allowed_regression_pct=2.0, alpha=0.01)

    # Simulated CI benchmark runs (50 samples each)
    import random
    random.seed(42)
    base_runs = [random.gauss(0.0120, 0.0004) for _ in range(50)]
    pr_runs = [random.gauss(0.0128, 0.0004) for _ in range(50)]  # ~6.6% slower

    passed = gate.evaluate_gate(base_runs, pr_runs)
    assert passed is False, "Gate should have blocked regression!"

from __future__ import annotations

import sys


def enforce_ci_release_gate(metrics: EvalRunMetrics) -> None:
    if not metrics.passed_ci_gate:
        print(
            f"CI GATE FAILED: recall={metrics.recall_at_k}, "
            f"acl_leaks={metrics.acl_leak_count}, pii_escapes={metrics.pii_escape_count}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    print("CI GATE PASSED: all compliance & recall thresholds satisfied.")


if __name__ == "__main__":
    passing = EvalRunMetrics(
        total_cases=3, recall_at_k=1.0, acl_leak_count=0, pii_escape_count=0, passed_ci_gate=True
    )
    enforce_ci_release_gate(passing)

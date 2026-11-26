from __future__ import annotations


def evaluate_coverage_gate(
    baseline_pct: float,
    post_patch_pct: float,
    min_floor_pct: float = 85.0,
    max_regression_pct: float = 0.5,
) -> tuple[bool, str]:
    if post_patch_pct < min_floor_pct:
        return False, f"Coverage {post_patch_pct:.2f}% is below floor {min_floor_pct:.2f}%"
    delta = post_patch_pct - baseline_pct
    if delta < -max_regression_pct:
        return False, f"Coverage regressed by {abs(delta):.2f}% (max allowed {max_regression_pct:.2f}%)"
    return True, f"Coverage passed: {post_patch_pct:.2f}% (delta {delta:+.2f}%)"


if __name__ == "__main__":
    for base, post in [(88.0, 91.4), (90.0, 88.2), (82.0, 83.5)]:
        ok, msg = evaluate_coverage_gate(base, post)
        print(f"ok={str(ok):<5} {msg}")

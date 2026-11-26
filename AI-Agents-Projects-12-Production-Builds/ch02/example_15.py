from __future__ import annotations

import json


def build_pr_audit_bundle(
    job_id: str,
    target_symbol: str,
    blast_radius: list[str],
    verdict: SandboxVerdict,
    unified_diff: str,
) -> str:
    approved = verdict.is_green and len(unified_diff.strip()) > 0
    bundle = {
        "job_id": job_id,
        "target_symbol": target_symbol,
        "blast_radius_modules": blast_radius,
        "sandbox_verdict": verdict.model_dump(),
        "diff_line_count": len(unified_diff.splitlines()),
        "pr_gate_approved": approved,
    }
    return json.dumps(bundle, indent=2)


if __name__ == "__main__":
    v = SandboxVerdict(
        run_id="sbx_4401",
        exit_code=0,
        tests_passed=18,
        tests_failed=0,
        coverage_pct=93.2,
        duration_ms=390.5,
    )
    payload = build_pr_audit_bundle(
        job_id="job_4401",
        target_symbol="billing.fees:compute_fee",
        blast_radius=["checkout.api", "jobs.nightly"],
        verdict=v,
        unified_diff="--- a/billing/fees.py\n+++ b/billing/fees.py\n@@ -1 +1 @@\n-pass\n+return 0\n",
    )
    print(payload)

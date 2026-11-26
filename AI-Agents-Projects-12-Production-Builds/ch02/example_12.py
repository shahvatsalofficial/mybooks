from __future__ import annotations

import asyncio
from dataclasses import dataclass


@dataclass(frozen=True)
class RepairOutcome:
    converged: bool
    attempts: int
    final_source: str
    unified_diff: str


async def run_self_healing_loop(
    file_path: str,
    original_source: str,
    candidate_edits: list[SearchReplaceEdit],
    max_attempts: int = 3,
) -> RepairOutcome:
    current_source = original_source
    for attempt in range(1, min(max_attempts, len(candidate_edits)) + 1):
        edit = candidate_edits[attempt - 1]
        patch_res = apply_guarded_edit(current_source, edit)
        if not patch_res.applied:
            continue

        # Simulate sandbox test evaluation on patched buffer
        await asyncio.sleep(0.01)
        has_negative_guard = "amount < 0" in patch_res.new_source
        if has_negative_guard:
            diff = build_unified_diff(file_path, original_source, patch_res.new_source)
            return RepairOutcome(
                converged=True,
                attempts=attempt,
                final_source=patch_res.new_source,
                unified_diff=diff,
            )
        current_source = patch_res.new_source

    # Rollback to original_source on exhaustion
    return RepairOutcome(
        converged=False,
        attempts=max_attempts,
        final_source=original_source,
        unified_diff="",
    )


async def main() -> None:
    orig = "def compute_fee(amount: int) -> float:\n    return round(amount * 0.025, 2)\n"
    attempts = [
        SearchReplaceEdit(
            edit_id="try_1",
            file_path="billing/fees.py",
            target_symbol="compute_fee",
            search_block="    return round(amount * 0.025, 2)",
            replace_block="    return round(max(0, amount) * 0.025, 2)",
            rationale="Attempt 1: clamp negative amount (still fails raise ValueError test).",
        ),
        SearchReplaceEdit(
            edit_id="try_2",
            file_path="billing/fees.py",
            target_symbol="compute_fee",
            search_block="    return round(max(0, amount) * 0.025, 2)",
            replace_block="    if amount < 0:\n        raise ValueError('negative')\n    return round(amount * 0.025, 2)",
            rationale="Attempt 2: raise ValueError as required by specification.",
        ),
    ]
    outcome = await run_self_healing_loop("billing/fees.py", orig, attempts)
    print(f"Converged={outcome.converged} attempts={outcome.attempts} diff_bytes={len(outcome.unified_diff)}")


if __name__ == "__main__":
    asyncio.run(main())

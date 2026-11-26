from __future__ import annotations

import asyncio
from difflib import get_close_matches
from typing import Dict, List
from pydantic import BaseModel, Field


class SchemaDriftFinding(BaseModel):
    table_fqn: str
    missing_columns: List[str] = Field(default_factory=list)
    renamed_candidates: Dict[str, str] = Field(default_factory=dict)
    null_rate_pct: Dict[str, float] = Field(default_factory=dict)


class SchemaDriftProbe:
    """Detects upstream column renames and null-rate spikes via diagnostic SQL."""

    async def inspect_table(
        self,
        table_fqn: str,
        expected_columns: List[str],
        actual_columns: List[str],
        null_counts: Dict[str, int],
        total_rows: int,
    ) -> SchemaDriftFinding:
        await asyncio.sleep(0.01)
        missing = [c for c in expected_columns if c not in actual_columns]
        renamed: Dict[str, str] = {}
        for m in missing:
            matches = get_close_matches(m, actual_columns, n=1, cutoff=0.55)
            if matches:
                renamed[m] = matches[0]

        null_rates: Dict[str, float] = {}
        denom = max(total_rows, 1)
        for col, n_cnt in null_counts.items():
            null_rates[col] = round((n_cnt / denom) * 100.0, 2)

        return SchemaDriftFinding(
            table_fqn=table_fqn,
            missing_columns=missing,
            renamed_candidates=renamed,
            null_rate_pct=null_rates,
        )


async def demo_drift_probe() -> None:
    probe = SchemaDriftProbe()
    finding = await probe.inspect_table(
        table_fqn="raw.card_events",
        expected_columns=["event_id", "merchant_id", "amount_cents"],
        actual_columns=["event_id", "merchant_acct_id", "amount_cents"],
        null_counts={"event_id": 0, "merchant_acct_id": 12, "amount_cents": 0},
        total_rows=250_000,
    )
    print(f"Table: {finding.table_fqn}")
    print(f"Missing: {finding.missing_columns} | Rename candidates: {finding.renamed_candidates}")
    print(f"Null rates (%): {finding.null_rate_pct}")


if __name__ == "__main__":
    asyncio.run(demo_drift_probe())

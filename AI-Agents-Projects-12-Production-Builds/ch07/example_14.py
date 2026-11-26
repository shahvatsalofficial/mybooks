from __future__ import annotations

import difflib
from pydantic import BaseModel


class DbtPatchProposal(BaseModel):
    model_name: str
    unified_diff: str
    verification_sql: str
    incident_summary: str


class DbtPatchGenerator:
    """Generates unified SQL diffs and regression checks for dbt schema drift."""

    def build_rename_patch(
        self,
        model_name: str,
        original_sql: str,
        old_col: str,
        new_col: str,
        relation_name: str,
    ) -> DbtPatchProposal:
        patched_sql = original_sql.replace(
            old_col, f"{new_col} AS {old_col}", 1
        )
        diff_lines = list(
            difflib.unified_diff(
                original_sql.splitlines(keepends=True),
                patched_sql.splitlines(keepends=True),
                fromfile=f"a/models/{model_name}.sql",
                tofile=f"b/models/{model_name}.sql",
            )
        )
        verification_sql = (
            f"SELECT COUNT(*) AS total_rows, "
            f"COUNT({old_col}) AS non_null_{old_col} "
            f"FROM {relation_name} LIMIT 1;"
        )
        summary = (
            f"Root cause isolated to `{model_name}`: upstream source renamed `{old_col}` "
            f"to `{new_col}`. Aliased `{new_col} AS {old_col}` to preserve downstream contracts."
        )
        return DbtPatchProposal(
            model_name=model_name,
            unified_diff="".join(diff_lines),
            verification_sql=verification_sql,
            incident_summary=summary,
        )


def demo_patch_generator() -> None:
    gen = DbtPatchGenerator()
    orig = "SELECT\n  event_id,\n  merchant_id,\n  amount_cents\nFROM raw.card_events\n"
    proposal = gen.build_rename_patch(
        model_name="stg_settlements",
        original_sql=orig,
        old_col="merchant_id",
        new_col="merchant_acct_id",
        relation_name="staging.stg_settlements",
    )
    print(proposal.incident_summary)
    print(proposal.unified_diff)
    print(f"Verification SQL: {proposal.verification_sql}")


if __name__ == "__main__":
    demo_patch_generator()

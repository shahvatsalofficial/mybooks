from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List
from pydantic import BaseModel


class InvestmentMemo(BaseModel):
    company_name: str
    cik: str
    accession_number: str
    generated_at: datetime
    executive_summary: str
    verified_metrics: Dict[str, str]
    source_citations: List[str]
    audit_passed: bool


class InvestmentMemoAssembler:
    """Compiles auditable investment memos with full XBRL provenance."""

    @staticmethod
    def assemble(
        company_name: str,
        cik: str,
        accession_number: str,
        metrics: Dict[str, str],
        citations: List[str],
        summary: str,
        audit_passed: bool,
    ) -> InvestmentMemo:
        if not audit_passed:
            raise ValueError("Cannot publish InvestmentMemo when numeric audit fails.")
        return InvestmentMemo(
            company_name=company_name,
            cik=cik,
            accession_number=accession_number,
            generated_at=datetime.now(timezone.utc),
            executive_summary=summary,
            verified_metrics=metrics,
            source_citations=citations,
            audit_passed=audit_passed,
        )


if __name__ == "__main__":
    memo = InvestmentMemoAssembler.assemble(
        company_name="Apex Semiconductor Corp",
        cik="0000950170",
        accession_number="0000950170-26-014210",
        metrics={"FCF_USD": "$1,700,000,000.00", "FCF_Margin": "13.24%", "Net_Leverage": "1.25x"},
        citations=["XBRL:0000950170-26-014210", "Note 9: Long-Term Debt"],
        summary="In 2025, Apex generated $1.70B FCF (13.24% margin) at 1.25x net leverage.",
        audit_passed=True,
    )
    print(memo.model_dump_json(indent=2))

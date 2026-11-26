from __future__ import annotations

import re
from decimal import Decimal
from typing import Dict, List, Optional
from pydantic import BaseModel


class CanonicalFinancialFact(BaseModel):
    metric: str
    gaap_tag: str
    fiscal_year: int
    fiscal_period: str
    value_usd: Decimal
    unit: str
    accession_number: str


class XbrlFactNormalizer:
    """Canonicalizes US-GAAP XBRL tags and resolves accounting sign conventions."""

    TAG_ALIASES: Dict[str, List[str]] = {
        "revenue": [
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "Revenues",
            "SalesRevenueNet",
        ],
        "operating_cash_flow": [
            "NetCashProvidedByUsedInOperatingActivities",
        ],
        "capex": [
            "PaymentsToAcquirePropertyPlantAndEquipment",
            "CapitalExpendituresIncurredButNotYetPaid",
        ],
        "net_income": [
            "NetIncomeLoss",
            "ProfitLoss",
        ],
    }

    PAREN_NUM_RE = re.compile(r"^\(\s*\$?\s*([\d,]+(?:\.\d+)?)\s*\)$")

    @classmethod
    def parse_accounting_number(cls, raw: str | int | float, scale_multiplier: int = 1) -> Decimal:
        if isinstance(raw, (int, float)):
            return Decimal(str(raw)) * Decimal(scale_multiplier)
        text = raw.strip()
        match = cls.PAREN_NUM_RE.match(text)
        if match:
            cleaned = match.group(1).replace(",", "")
            return -Decimal(cleaned) * Decimal(scale_multiplier)
        cleaned = text.replace("$", "").replace(",", "").strip()
        return Decimal(cleaned) * Decimal(scale_multiplier)

    def resolve_metric(
        self, raw_facts: Dict[str, Dict[str, Decimal]], canonical_metric: str
    ) -> Optional[str]:
        candidates = self.TAG_ALIASES.get(canonical_metric, [])
        for tag in candidates:
            if tag in raw_facts:
                return tag
        return None


if __name__ == "__main__":
    normalizer = XbrlFactNormalizer()
    capex_val = normalizer.parse_accounting_number("(1,420.50)", scale_multiplier=1_000_000)
    rev_val = normalizer.parse_accounting_number("$12,840.00", scale_multiplier=1_000_000)
    tag = normalizer.resolve_metric(
        {"RevenueFromContractWithCustomerExcludingAssessedTax": {"FY2025": rev_val}},
        "revenue",
    )
    print(f"Resolved revenue tag: {tag}")
    print(f"Parsed CapEx (USD): {capex_val}")
    print(f"Parsed Revenue (USD): {rev_val}")

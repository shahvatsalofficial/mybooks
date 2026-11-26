from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from pydantic import BaseModel


class VarianceBridge(BaseModel):
    metric: str
    prior_usd: Decimal
    current_usd: Decimal
    delta_usd: Decimal
    delta_pct: Decimal


class CrossPeriodVarianceAnalyzer:
    """Computes deterministic YoY/QoQ dollar and percentage variance bridges."""

    @staticmethod
    def compute_bridge(metric: str, prior_usd: Decimal, current_usd: Decimal) -> VarianceBridge:
        if prior_usd == 0:
            raise ValueError(f"Prior period value for '{metric}' cannot be zero.")
        delta = current_usd - prior_usd
        pct = ((delta / abs(prior_usd)) * Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return VarianceBridge(
            metric=metric,
            prior_usd=prior_usd,
            current_usd=current_usd,
            delta_usd=delta,
            delta_pct=pct,
        )


if __name__ == "__main__":
    bridges = [
        CrossPeriodVarianceAnalyzer.compute_bridge("Revenue", Decimal("11200000000"), Decimal("12840000000")),
        CrossPeriodVarianceAnalyzer.compute_bridge("Operating_Cash_Flow", Decimal("2640000000"), Decimal("3120000000")),
        CrossPeriodVarianceAnalyzer.compute_bridge("CapEx_Outflow", Decimal("-980000000"), Decimal("-1420000000")),
    ]
    for b in bridges:
        print(b.model_dump_json())

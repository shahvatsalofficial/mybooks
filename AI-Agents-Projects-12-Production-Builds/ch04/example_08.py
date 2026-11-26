from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from pydantic import BaseModel


class FinancialMetricsOutput(BaseModel):
    free_cash_flow_usd: Decimal
    fcf_margin_pct: Decimal
    yoy_revenue_growth_pct: Decimal
    net_leverage_ratio: Decimal


class DecimalFinancialEngine:
    """Computes exact fixed-point financial metrics using decimal.Decimal."""

    @staticmethod
    def _quantize(val: Decimal, places: str = "0.01") -> Decimal:
        return val.quantize(Decimal(places), rounding=ROUND_HALF_UP)

    @classmethod
    def compute(
        cls,
        revenue_curr: Decimal,
        revenue_prev: Decimal,
        operating_cash_flow: Decimal,
        capex_negative: Decimal,
        total_debt: Decimal,
        cash_and_equiv: Decimal,
        ebitda: Decimal,
    ) -> FinancialMetricsOutput:
        if revenue_curr <= 0 or revenue_prev <= 0 or ebitda <= 0:
            raise ValueError("Denominators (revenue, ebitda) must be strictly positive.")
        if capex_negative > 0:
            raise ValueError("CapEx must be passed as negative outflow to prevent sign inversion.")

        fcf = operating_cash_flow + capex_negative
        fcf_margin = (fcf / revenue_curr) * Decimal("100")
        yoy_growth = ((revenue_curr - revenue_prev) / revenue_prev) * Decimal("100")
        net_debt = total_debt - cash_and_equiv
        net_leverage = net_debt / ebitda

        return FinancialMetricsOutput(
            free_cash_flow_usd=cls._quantize(fcf),
            fcf_margin_pct=cls._quantize(fcf_margin),
            yoy_revenue_growth_pct=cls._quantize(yoy_growth),
            net_leverage_ratio=cls._quantize(net_leverage),
        )


if __name__ == "__main__":
    out = DecimalFinancialEngine.compute(
        revenue_curr=Decimal("12840000000"),
        revenue_prev=Decimal("11200000000"),
        operating_cash_flow=Decimal("3120000000"),
        capex_negative=Decimal("-1420000000"),
        total_debt=Decimal("4800000000"),
        cash_and_equiv=Decimal("1100000000"),
        ebitda=Decimal("2950000000"),
    )
    print(out.model_dump_json(indent=2))

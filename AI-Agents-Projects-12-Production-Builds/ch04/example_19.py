from decimal import Decimal, ROUND_HALF_UP

def ebitda_margin_pct(ebitda: Decimal, revenue: Decimal) -> Decimal:
    if revenue <= 0:
        raise ValueError("Revenue must be positive.")
    return ((ebitda / revenue) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

print("EBITDA Margin %:", ebitda_margin_pct(Decimal("2950000000"), Decimal("12840000000")))

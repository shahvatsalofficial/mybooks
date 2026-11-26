from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import List


class SensitivityMatrixBuilder:
    """Generates deterministic terminal-value sensitivity grids across WACC and g."""

    @staticmethod
    def build_grid(
        base_fcf_millions: Decimal,
        wacc_rates: List[Decimal],
        growth_rates: List[Decimal],
    ) -> List[List[str]]:
        grid: List[List[str]] = []
        for wacc in wacc_rates:
            row: List[str] = []
            for g in growth_rates:
                if wacc <= g:
                    row.append("N/A")
                else:
                    tv = (base_fcf_millions * (Decimal("1") + g)) / (wacc - g)
                    row.append(f"${tv.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP):,}M")
            grid.append(row)
        return grid


if __name__ == "__main__":
    waccs = [Decimal("0.085"), Decimal("0.095"), Decimal("0.105")]
    growths = [Decimal("0.020"), Decimal("0.025"), Decimal("0.030")]
    matrix = SensitivityMatrixBuilder.build_grid(Decimal("1700"), waccs, growths)
    for w, r in zip(waccs, matrix):
        print(f"WACC {w*100:.1f}% -> {r}")

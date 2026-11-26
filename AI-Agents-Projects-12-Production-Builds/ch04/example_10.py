from __future__ import annotations

from decimal import Decimal
from enum import Enum


class ScaleUnit(str, Enum):
    EXACT = "exact"
    THOUSANDS = "thousands"
    MILLIONS = "millions"
    BILLIONS = "billions"


class CurrencyAndUnitNormalizer:
    """Converts scaled table numbers into exact base USD Decimal values."""

    MULTIPLIERS = {
        ScaleUnit.EXACT: Decimal("1"),
        ScaleUnit.THOUSANDS: Decimal("1000"),
        ScaleUnit.MILLIONS: Decimal("1000000"),
        ScaleUnit.BILLIONS: Decimal("1000000000"),
    }

    @classmethod
    def to_base_usd(cls, amount: Decimal, unit: ScaleUnit) -> Decimal:
        return amount * cls.MULTIPLIERS[unit]


if __name__ == "__main__":
    rev = CurrencyAndUnitNormalizer.to_base_usd(Decimal("12.84"), ScaleUnit.BILLIONS)
    capex = CurrencyAndUnitNormalizer.to_base_usd(Decimal("-1420"), ScaleUnit.MILLIONS)
    print(f"Revenue (USD): {rev:,}")
    print(f"CapEx (USD):   {capex:,}")

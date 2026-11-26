from __future__ import annotations

from decimal import Decimal
from pydantic import BaseModel


class IdentityCheckResult(BaseModel):
    balanced: bool
    discrepancy_usd: Decimal
    message: str


class VarianceGatekeeper:
    """Validates accounting identities within strict rounding tolerances."""

    @staticmethod
    def check_balance_sheet(
        total_assets: Decimal,
        total_liabilities: Decimal,
        total_equity: Decimal,
        tolerance_usd: Decimal = Decimal("1000000"),
    ) -> IdentityCheckResult:
        diff = abs(total_assets - (total_liabilities + total_equity))
        ok = diff <= tolerance_usd
        msg = "Balance sheet identity verified." if ok else f"Imbalance detected: ${diff:,} exceeds tolerance."
        return IdentityCheckResult(balanced=ok, discrepancy_usd=diff, message=msg)


if __name__ == "__main__":
    ok = VarianceGatekeeper.check_balance_sheet(
        Decimal("18500000000"), Decimal("10200000000"), Decimal("8300000000")
    )
    print(ok.model_dump_json())

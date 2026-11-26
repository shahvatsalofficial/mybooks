from collections import defaultdict
from typing import Dict

class RateLimitedPolicyGuard:
    def __init__(self, max_daily_credits_per_tenant: int = 3) -> None:
        self._max_count = max_daily_credits_per_tenant
        self._counts: Dict[str, int] = defaultdict(int)

    def allow_credit(self, tenant_id: str, amount_usd: float, cap_usd: float) -> bool:
        if amount_usd > cap_usd or self._counts[tenant_id] >= self._max_count:
            return False
        self._counts[tenant_id] += 1
        return True

guard = RateLimitedPolicyGuard(max_daily_credits_per_tenant=3)
print([guard.allow_credit("ten_1", 20.0, 50.0) for _ in range(4)])

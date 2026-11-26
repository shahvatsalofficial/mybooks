# remediation_checkout_governor.py
# Production architectural fix: Enforces jittered backoff and secondary gateway failover.

import random
import time
from typing import Dict, Any, Tuple


class ResilientCheckoutGovernor:
    """Enforces non-negotiable backoff and gateway failover on payment retries."""

    MAX_RETRIES_PER_GATEWAY = 2

    def __init__(self, stripe_client: Any, adyen_client: Any):
        self.stripe = stripe_client
        self.adyen = adyen_client

    def execute_resilient_payment(self, payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Executes payment with jittered retry and secondary gateway failover."""
        # 1. Primary Attempt (Stripe)
        for attempt in range(self.MAX_RETRIES_PER_GATEWAY):
            try:
                res = self.stripe.authorize(payload)
                return True, {"gateway": "STRIPE", "data": res}
            except Exception:
                # Full Jitter Sleep
                sleep_dur = random.uniform(0.5, 1.0 * (2.0 ** attempt))
                time.sleep(sleep_dur)

        # 2. Secondary Gateway Failover (Adyen)
        try:
            res = self.adyen.authorize(payload)
            return True, {"gateway": "ADYEN_FAILOVER", "data": res}
        except Exception as exc:
            return False, {"error": f"Both gateways exhausted: {str(exc)}"}

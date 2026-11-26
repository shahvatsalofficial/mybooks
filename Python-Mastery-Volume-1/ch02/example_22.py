# THE REFACTORED PRODUCTION PIPELINE
from typing import Sequence, Optional

class SubscriptionService:
    def process_billing_batch(self, accounts: Sequence[Account]) -> BatchBillingSummary:
        """
        1. Enforces Sequence[Account] (Covariant, read-only).
        2. Strictly prohibits passing list[Any] or modifying input collections.
        """
        success_count = 0
        skipped_count = 0

        for account in accounts:
            subscription: Optional[Subscription] = account.get_active_subscription()

            # Compile-time narrowing enforced: Mypy rejects direct access without check!
            if subscription is None:
                skipped_count += 1
                logger.info(f"Skipping account {account.id}: No active subscription found.")
                continue

            # Mypy proves 'subscription' is non-null Subscription
            self._execute_charge(subscription)
            success_count += 1

        return BatchBillingSummary(success_count=success_count, skipped_count=skipped_count)

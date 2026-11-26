# THE DEFECTIVE LEGACY IMPLEMENTATION
class SubscriptionService:
    def process_billing_batch(self, accounts: list) -> None:
        # Flaw 1: 'accounts: list' defaults to list[Any] due to missing generics
        for account in accounts:
            subscription = account.get_active_subscription()
            # Flaw 2: get_active_subscription() returned Subscription | None
            # But the developer assumed it never returned None:
            self._execute_charge(subscription)

    def _execute_charge(self, sub: Subscription) -> None:
        # Flaw 3: In non-strict Mypy, passing None to 'sub: Subscription' 
        # was permitted because of legacy 'implicit optional' behavior!
        sub.charge()  # DETONATES: AttributeError: 'NoneType' object has no attribute 'charge'

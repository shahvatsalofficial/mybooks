import signal

class GracefulDrainGovernor:
    def __init__(self, grace_period_sec: float = 15.0):
        self.grace_period = grace_period_sec
        self.is_draining = False
        self.active_transactions = 0

    def handle_sigterm(self, signum, frame):
        print("
[DRAIN SIGNAL] SIGTERM received. Halting ingress, draining active agent turns...")
        self.is_draining = True

    def begin_transaction(self) -> bool:
        if self.is_draining:
            return False # Reject new requests
        self.active_transactions += 1
        return True

    def complete_transaction(self):
        self.active_transactions = max(0, self.active_transactions - 1)

# Verification
drain_gov = GracefulDrainGovernor()
drain_gov.begin_transaction()
print("Active Turns in Flight:", drain_gov.active_transactions)
drain_gov.handle_sigterm(signal.SIGTERM, None)
print("Can accept new turn post-SIGTERM?", drain_gov.begin_transaction())
drain_gov.complete_transaction()
print("Remaining Active Turns post-drain:", drain_gov.active_transactions)

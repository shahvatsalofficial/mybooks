class DualTokenBucket:
    def __init__(self, rpm_capacity: float, tpm_capacity: float):
        self.rpm = LeakyTokenBucket(capacity=rpm_capacity, refill_rate_per_sec=rpm_capacity / 60.0)
        self.tpm = LeakyTokenBucket(capacity=tpm_capacity, refill_rate_per_sec=tpm_capacity / 60.0)

    def consume(self, requests: float, tokens: float) -> bool:
        if self.rpm.acquire(requests):
            if self.tpm.acquire(tokens):
                return True
            # Refund request token if token budget fails
            self.rpm.tokens += requests
        return False

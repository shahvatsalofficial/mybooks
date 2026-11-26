class HallucinationMetrics:
    def __init__(self):
        self.verified_claims = 0
        self.unverified_claims = 0

    def record_claim(self, is_verified: bool):
        if is_verified:
            self.verified_claims += 1
        else:
            self.unverified_claims += 1

    @property
    def hallucination_rate(self) -> float:
        total = self.verified_claims + self.unverified_claims
        return self.unverified_claims / max(1, total)

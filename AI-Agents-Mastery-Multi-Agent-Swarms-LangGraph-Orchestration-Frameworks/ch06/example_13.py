class ReplayAttackDefender:
    def __init__(self):
        self.seen_nonces: set[str] = set()

    def verify_nonce(self, nonce: str) -> bool:
        if nonce in self.seen_nonces:
            raise PermissionError(f"Replay attack detected! Nonce '{nonce}' already used.")
        self.seen_nonces.add(nonce)
        return True

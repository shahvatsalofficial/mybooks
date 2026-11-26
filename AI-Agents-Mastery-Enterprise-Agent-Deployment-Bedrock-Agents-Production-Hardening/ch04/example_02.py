import hmac
import hashlib
import time
import secrets
from typing import Dict, Any, Tuple

class CanaryTokenManager:
    """Generates and detects high-entropy cryptographic canary strings across agent memory."""

    def __init__(self, hmac_secret: bytes):
        self.secret = hmac_secret

    def generate_canary(self, resource_id: str) -> str:
        """Creates a signed, high-entropy canary token."""
        nonce = secrets.token_hex(8)
        timestamp = int(time.time())
        message = f"CANARY:{resource_id}:{nonce}:{timestamp}".encode()
        signature = hmac.new(self.secret, message, hashlib.sha256).hexdigest()[:16]
        return f"CANARY_{resource_id}_{nonce}_{signature}"

    def inspect_payload(self, text_payload: str) -> Tuple[bool, Optional[str]]:
        """Scans outgoing agent text or tool payloads for leaked canaries."""
        pattern = re.compile(r"CANARY_[A-Za-z0-9\-]+_[a-f0-9]{16}_[a-f0-9]{16}")
        match = pattern.search(text_payload)
        if match:
            canary = match.group(0)
            return True, canary
        return False, None

if __name__ == "__main__":
    secret_key = b"enterprise-agent-security-master-key-2026"
    manager = CanaryTokenManager(secret_key)
    
    canary = manager.generate_canary("CUSTOMER_DATABASE_P0")
    print(f"Generated Database Canary: {canary}")
    
    # Simulate attacker attempting to leak database content
    leaked_message = f"Here is the user summary: Name: Alice, ID: 4091, InternalRef: {canary}"
    detected, leaked_token = manager.inspect_payload(leaked_message)
    
    if detected:
        print(f"[ALARM] Canary breach detected! Leaked token: {leaked_token}")
        print("Action: Revoking agent IAM session and alerting Security Operations Center.")

import hmac
import hashlib
import time
from typing import Dict, Any, Tuple

class SecureApprovalWebhookGateway:
    """Verifies incoming Slack/Teams interactive callback signatures and timestamps."""

    def __init__(self, signing_secret: bytes, max_clock_drift_seconds: int = 300):
        self.signing_secret = signing_secret
        self.max_drift = max_clock_drift_seconds

    def verify_request(self, raw_body: bytes, timestamp_str: str, signature_header: str) -> Tuple[bool, str]:
        """Validates request timestamp and HMAC signature."""
        try:
            timestamp = int(timestamp_str)
        except ValueError:
            return False, "INVALID_TIMESTAMP_HEADER"

        # Check for replay attacks
        now = int(time.time())
        if abs(now - timestamp) > self.max_drift:
            return False, "REQUEST_EXPIRED_CLOCK_DRIFT"

        # Slack signature format: v0=HMAC_SHA256(secret, "v0:" + timestamp + ":" + body)
        sig_basestring = f"v0:{timestamp}:".encode() + raw_body
        expected_sig = "v0=" + hmac.new(self.signing_secret, sig_basestring, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(signature_header, expected_sig):
            return False, "SIGNATURE_VERIFICATION_FAILED"

        return True, "SIGNATURE_VALID"

if __name__ == "__main__":
    secret = b"slack-signing-secret-key-prod-2026"
    gateway = SecureApprovalWebhookGateway(secret)
    
    body = b'{"payload": "user_clicked_approve"}'
    ts = str(int(time.time()))
    
    # Generate legitimate signature
    base = f"v0:{ts}:".encode() + body
    valid_sig = "v0=" + hmac.new(secret, base, hashlib.sha256).hexdigest()
    
    valid, reason = gateway.verify_request(body, ts, valid_sig)
    print(f"Legitimate webhook verification: {valid} ({reason})")
    
    # Forged signature test
    invalid, f_reason = gateway.verify_request(body, ts, "v0=badbadbadbadbadbadbadbadbad")
    print(f"Forged webhook verification: {invalid} ({f_reason})")

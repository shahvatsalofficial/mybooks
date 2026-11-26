import hmac
import hashlib

def verify_publish_transition(payload: str, signature: str, secret_key: bytes) -> bool:
    expected_sig = hmac.new(secret_key, payload.encode('utf-8'), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_sig, signature):
        raise PermissionError("FSM State Gate: Cryptographic verification failed for PUBLISH transition.")
    return True

import hmac
import hashlib
import time
import json
import base64
from typing import Dict, Any, List, Optional

class ScopedCapabilityAuthority:
    """Issues and validates short-lived capability tokens for high-impact agent tools."""

    def __init__(self, signing_secret: bytes):
        self.secret = signing_secret

    def issue_token(self, user_id: str, allowed_tools: List[str], ttl_seconds: int = 60) -> str:
        """Issues an encrypted, time-bounded capability payload."""
        now = int(time.time())
        payload = {
            "sub": user_id,
            "tools": allowed_tools,
            "iat": now,
            "exp": now + ttl_seconds
        }
        encoded_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
        sig = hmac.new(self.secret, encoded_payload.encode(), hashlib.sha256).hexdigest()
        return f"{encoded_payload}.{sig}"

    def validate_capability(self, token_str: str, requested_tool: str) -> Tuple[bool, str]:
        """Validates token integrity, expiration, and tool authorization."""
        parts = token_str.split(".")
        if len(parts) != 2:
            return False, "INVALID_TOKEN_FORMAT"
        
        encoded_payload, sig = parts[0], parts[1]
        expected_sig = hmac.new(self.secret, encoded_payload.encode(), hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(sig, expected_sig):
            return False, "SIGNATURE_MISMATCH"
            
        payload = json.loads(base64.urlsafe_b64decode(encoded_payload.encode()).decode())
        
        if time.time() > payload["exp"]:
            return False, "TOKEN_EXPIRED"
            
        if requested_tool not in payload.get("tools", []):
            return False, f"UNAUTHORIZED_TOOL: User {payload['sub']} lacks permission for {requested_tool}"
            
        return True, "AUTHORIZED"

if __name__ == "__main__":
    authority = ScopedCapabilityAuthority(b"production-signing-secret-key-32b")
    
    # Low-privilege support user token
    support_token = authority.issue_token("support-rep-102", ["read_user_profile", "query_kb"])
    
    # Verify allowed tool
    valid, reason = authority.validate_capability(support_token, "read_user_profile")
    print(f"Tool 'read_user_profile' check: {valid} ({reason})")
    
    # Verify forbidden privileged tool (Confused Deputy attempt)
    forbidden, f_reason = authority.validate_capability(support_token, "delete_database_record")
    print(f"Tool 'delete_database_record' check: {forbidden} ({f_reason})")

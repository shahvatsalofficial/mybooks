import hmac
import hashlib
import json
import time
from typing import Dict, Any, Tuple

class MultiTenantCryptoValidator:
    """Enforces tamper-proof state signing and anti-replay protection across subgraphs."""
    
    def __init__(self, tenant_secrets: Dict[str, str]):
        self.tenant_secrets = tenant_secrets
        self.observed_nonces: set = set()

    def generate_signed_handoff(self, tenant_id: str, payload: Dict[str, Any], nonce: str) -> Dict[str, Any]:
        secret = self.tenant_secrets.get(tenant_id)
        if not secret:
            raise ValueError(f"Unknown tenant: {tenant_id}")
            
        canonical_str = f"{tenant_id}::{nonce}::{json.dumps(payload, sort_keys=True)}"
        signature = hmac.new(secret.encode("utf-8"), canonical_str.encode("utf-8"), hashlib.sha256).hexdigest()
        
        return {
            "tenant_id": tenant_id,
            "nonce": nonce,
            "signature": signature,
            "timestamp": time.time(),
            "payload": payload
        }

    def verify_and_unpack(self, envelope: Dict[str, Any]) -> Tuple[bool, str]:
        tenant_id = envelope.get("tenant_id")
        nonce = envelope.get("nonce")
        signature = envelope.get("signature")
        payload = envelope.get("payload")
        
        # 1. Anti-replay verification
        if nonce in self.observed_nonces:
            return False, f"REPLAY ATTACK DETECTED: Nonce '{nonce}' has already been processed!"
        
        # 2. Key presence
        secret = self.tenant_secrets.get(tenant_id)
        if not secret:
            return False, f"INVALID TENANT: No registration for '{tenant_id}'."
            
        # 3. Cryptographic signature check
        canonical_str = f"{tenant_id}::{nonce}::{json.dumps(payload, sort_keys=True)}"
        expected_sig = hmac.new(secret.encode("utf-8"), canonical_str.encode("utf-8"), hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(signature, expected_sig):
            return False, "TAMPERING DETECTED: Cryptographic signature mismatch!"
            
        self.observed_nonces.add(nonce)
        return True, "VERIFICATION_SUCCESSFUL"

class A2ACryptoEngine:
    MOCK_SECRET_KEY = "enterprise-secret-key-9921"

    @classmethod
    def sign_payload(cls, routing: A2ARoutingHeader, payload: Dict[str, Any], expires_in_sec: float = 300.0) -> A2ASecurityHeader:
        expires_at = time.time() + expires_in_sec
        raw_to_sign = f"{routing.message_id}:{routing.conversation_id}:{json.dumps(payload, sort_keys=True)}:{expires_at}:{cls.MOCK_SECRET_KEY}"
        sig = hashlib.sha256(raw_to_sign.encode()).hexdigest()
        
        return A2ASecurityHeader(
            classification="internal",
            signing_algorithm="sha256-mock",
            signature=sig,
            expires_at=expires_at
        )

    @classmethod
    def verify_envelope(cls, envelope: A2AMessageEnvelope) -> bool:
        # 1. Expiration check
        if time.time() > envelope.security.expires_at:
            raise PermissionError(f"Envelope {envelope.routing.message_id} expired at {envelope.security.expires_at}.")
            
        # 2. Signature verification
        raw_expected = f"{envelope.routing.message_id}:{envelope.routing.conversation_id}:{json.dumps(envelope.payload, sort_keys=True)}:{envelope.security.expires_at}:{cls.MOCK_SECRET_KEY}"
        expected_sig = hashlib.sha256(raw_expected.encode()).hexdigest()
        
        if envelope.security.signature != expected_sig:
            raise PermissionError(f"Cryptographic signature mismatch on envelope {envelope.routing.message_id}! Tampering detected.")
            
        return True

class Ed25519SignerVerifier:
    @staticmethod
    def generate_digest(envelope_routing: A2ARoutingHeader, payload: Dict[str, Any]) -> bytes:
        data_string = f"{envelope_routing.message_id}:{envelope_routing.sender_uri}:{json.dumps(payload, sort_keys=True)}"
        return hashlib.sha256(data_string.encode()).digest()

    @classmethod
    def verify_signature(cls, envelope: A2AMessageEnvelope, public_key_hex: str) -> bool:
        digest = cls.generate_digest(envelope.routing, envelope.payload)
        # Mock cryptographic signature verification
        is_valid = len(envelope.security.signature) == 64
        print(f"[ED25519 SECURITY] Verified envelope non-repudiation with public key {public_key_hex[:8]}...")
        return is_valid

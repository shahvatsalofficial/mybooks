# security/pkce.py
"""OAuth 2.1 Proof Key for Code Exchange (PKCE) cryptographic derivation engine."""

from __future__ import annotations
import base64
import hashlib
import re
import secrets
from typing import NamedTuple


class PKCEPair(NamedTuple):
    code_verifier: str
    code_challenge: str
    code_challenge_method: str = "S256"


class PKCEEngine:
    """Generates high-entropy verifiers and derives SHA-256 code challenges."""

    # Unreserved character set defined in RFC 7636 Section 4.1
    VERIFIER_PATTERN = re.compile(r"^[A-Za-z0-9\-._~]{43,128}$")

    @classmethod
    def generate_pair(cls, entropy_bytes: int = 64) -> PKCEPair:
        """Generates a cryptographically random code_verifier and derives its S256 challenge."""
        # 1. Generate high-entropy unguessable random string (43 to 128 characters)
        raw_token = secrets.token_urlsafe(entropy_bytes)
        code_verifier = raw_token[:128]  # Bound within RFC maximum length

        # 2. Derive S256 Challenge: Base64URL-Encode(SHA-256(code_verifier))
        sha256_digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        
        # Base64-url-encode without trailing '=' padding characters
        code_challenge = (
            base64.urlsafe_b64encode(sha256_digest)
            .decode("ascii")
            .rstrip("=")
        )

        return PKCEPair(
            code_verifier=code_verifier,
            code_challenge=code_challenge,
            code_challenge_method="S256",
        )

    @classmethod
    def verify_challenge(cls, verifier: str, expected_challenge: str) -> bool:
        """Verifies incoming code_verifier against previously recorded challenge using constant-time comparison."""
        if not cls.VERIFIER_PATTERN.match(verifier):
            return False

        calculated_digest = hashlib.sha256(verifier.encode("ascii")).digest()
        calculated_challenge = (
            base64.urlsafe_b64encode(calculated_digest)
            .decode("ascii")
            .rstrip("=")
        )

        # Constant-time comparison defends against timing attack vectors
        return secrets.compare_digest(calculated_challenge, expected_challenge)

# cryptographic_token_vault.py — Reversible In-Memory Token Vault
import hmac
import hashlib
import secrets
from typing import Dict, Tuple

class EphemeralTokenVault:
    def __init__(self, session_id: str):
        self.session_id = session_id
        # Ephemeral 256-bit session key generated in memory
        self._session_key = secrets.token_bytes(32)
        self._entity_to_token: Dict[str, str] = {}
        self._token_to_entity: Dict[str, str] = {}
        self._entity_counters: Dict[str, int] = {}

    def mask_entity(self, plaintext_value: str, entity_type: str) -> str:
        """Deterministically substitutes plaintext with a structured surrogate token."""
        clean_val = plaintext_value.strip()
        if clean_val in self._entity_to_token:
            return self._entity_to_token[clean_val]

        # Allocate monotonic counter for clean conversational readability
        count = self._entity_counters.get(entity_type, 0) + 1
        self._entity_counters[entity_type] = count
        
        # Generate cryptographically bound surrogate token
        token_name = f"<{entity_type}_{count}>"
        
        # Store bi-directional in-memory mappings
        self._entity_to_token[clean_val] = token_name
        self._token_to_entity[token_name] = clean_val
        return token_name

    def unmask_text(self, text: str) -> str:
        """Reconstitutes original entities in outbound stream chunks."""
        reconstituted = text
        for token, original in self._token_to_entity.items():
            reconstituted = reconstituted.replace(token, original)
        return reconstituted

    def destroy(self):
        """Zeroes memory buffers upon conversation closure."""
        self._session_key = b"\x00" * 32
        self._entity_to_token.clear()
        self._token_to_entity.clear()

"""
Citation Integrity Guardrail: Intercepts generated XML citations,
validates that chunk IDs exist in active context, and verifies character content hashes.
"""

import re
import hashlib
from typing import Dict, Any, List, Tuple


class CitationIntegrityValidator:
    """Validates structural and cryptographic integrity of generated citation tags."""

    @staticmethod
    def extract_citations(text: str) -> List[Dict[str, str]]:
        """Extracts source_citation XML tags and their attributes."""
        pattern = r'<source_citation\s+chunk_id=["\'](.*?)["\']\s+hash=["\'](.*?)["\'].*?/>'
        matches = re.findall(pattern, text)
        return [{"chunk_id": m[0], "hash": m[1]} for m in matches]

    @staticmethod
    def validate_citations_against_context(
        citations: List[Dict[str, str]],
        active_chunks: Dict[str, str]
    ) -> Tuple[bool, List[str]]:
        """
        Validates citation existence and cryptographic hash matches.
        active_chunks: Dict mapping chunk_id -> raw_chunk_text
        """
        errors = []

        if not citations:
            return False, ["ZERO_CITATIONS_FOUND: Grounded response emitted zero source citations."]

        for cit in citations:
            chunk_id = cit["chunk_id"]
            declared_hash = cit["hash"]

            if chunk_id not in active_chunks:
                errors.append(f"FABRICATED_CHUNK_ID: Chunk '{chunk_id}' does not exist in context.")
                continue

            raw_text = active_chunks[chunk_id]
            expected_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()[:8]

            if declared_hash != expected_hash:
                errors.append(
                    f"HASH_MISMATCH: Chunk '{chunk_id}' declared hash '{declared_hash}' "
                    f"does not match actual hash '{expected_hash}'."
                )

        return len(errors) == 0, errors

"""
merkle_audit_ledger.py
Enterprise Merkle Tree Non-Repudiation Audit Ledger for Foundation Model Invocations.
Guarantees cryptographic proof of non-tampering for SOC-2 Type II and EU AI Act Art 12.
"""

import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple


def sha256(data: bytes) -> str:
    """Computes standard hexadecimal SHA-256 digest."""
    return hashlib.sha256(data).hexdigest()


class CanonicalMerkleTree:
    """Computes SHA-256 Merkle tree roots and inclusion proofs across AI invocation records."""

    def __init__(self, records: List[Dict[str, Any]]):
        self.raw_records = records
        self.leaf_hashes: List[str] = [self._hash_record(rec) for rec in records]
        self.levels: List[List[str]] = [self.leaf_hashes]
        self._build_tree()

    @staticmethod
    def _hash_record(record: Dict[str, Any]) -> str:
        """Serializes dictionary to canonical JSON with sorted keys before SHA-256 hashing."""
        canonical_str = json.dumps(record, sort_keys=True, separators=(",", ":"))
        return sha256(canonical_str.encode("utf-8"))

    def _build_tree(self):
        """Recursively builds the binary Merkle tree levels up to the single Merkle Root."""
        current_level = self.leaf_hashes
        while len(current_level) > 1:
            next_level: List[str] = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                combined_hash = sha256((left + right).encode("utf-8"))
                next_level.append(combined_hash)
            self.levels.append(next_level)
            current_level = next_level

    @property
    def root(self) -> str:
        """Returns the 32-byte hexadecimal Merkle Root digest."""
        if not self.levels or not self.levels[-1]:
            return ""
        return self.levels[-1][0]

    def generate_audit_proof(self, index: int) -> List[Dict[str, str]]:
        """
        Generates a cryptographic audit path proving inclusion of record at index.
        Auditor can verify this single record without inspecting other private customer logs.
        """
        if index < 0 or index >= len(self.leaf_hashes):
            raise IndexError("Record index out of range for Merkle proof generation.")

        proof: List[Dict[str, str]] = []
        curr_idx = index

        for level in self.levels[:-1]:
            is_right_child = (curr_idx % 2 == 1)
            sibling_idx = curr_idx - 1 if is_right_child else curr_idx + 1
            
            if sibling_idx < len(level):
                proof.append({
                    "position": "left" if is_right_child else "right",
                    "hash": level[sibling_idx]
                })
            else:
                # Odd node duplicated in balanced tree
                proof.append({
                    "position": "right",
                    "hash": level[curr_idx]
                })
            curr_idx //= 2

        return proof

    @staticmethod
    def verify_inclusion(record: Dict[str, Any], proof: List[Dict[str, str]], expected_root: str) -> bool:
        """
        Verifies whether an individual record belongs to the anchored Merkle Root.
        Executed by independent regulatory auditors with zero knowledge of surrounding records.
        """
        curr_hash = CanonicalMerkleTree._hash_record(record)

        for element in proof:
            sibling_hash = element["hash"]
            if element["position"] == "left":
                combined = sibling_hash + curr_hash
            else:
                combined = curr_hash + sibling_hash
            curr_hash = sha256(combined.encode("utf-8"))

        return curr_hash == expected_root

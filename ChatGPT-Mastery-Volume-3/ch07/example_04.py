# merkle_provenance_verifier.py — Cryptographic Model Supply Chain
import hashlib
import json
import os
from typing import List, Dict, Any

class MerkleProvenanceLedger:
    def __init__(self):
        self.leaves: List[str] = []
        self.audit_log: List[Dict[str, Any]] = []

    def _hash_file(self, file_path: str) -> str:
        """Computes SHA-256 hash of a dataset or weight file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                sha256.update(chunk)
        return sha256.hexdigest()

    def add_artifact(self, artifact_name: str, file_path: str, artifact_type: str):
        file_hash = self._hash_file(file_path)
        leaf_payload = f"{artifact_type}:{artifact_name}:{file_hash}"
        leaf_hash = hashlib.sha256(leaf_payload.encode('utf-8')).hexdigest()
        
        self.leaves.append(leaf_hash)
        self.audit_log.append({
            "artifact_name": artifact_name,
            "artifact_type": artifact_type,
            "sha256": file_hash,
            "leaf_hash": leaf_hash,
            "size_bytes": os.path.getsize(file_path)
        })

    def compute_root(self) -> str:
        """Recursively hashes leaves to compute immutable Merkle Root."""
        if not self.leaves:
            return ""

        current_layer = self.leaves
        while len(current_layer) > 1:
            next_layer = []
            for i in range(0, len(current_layer), 2):
                left = current_layer[i]
                right = current_layer[i + 1] if i + 1 < len(current_layer) else left
                combined = hashlib.sha256((left + right).encode('utf-8')).hexdigest()
                next_layer.append(combined)
            current_layer = next_layer

        return current_layer[0]

    def export_attestation(self, output_path: str):
        root_hash = self.compute_root()
        manifest = {
            "spec_version": "https://slsa.dev/provenance/v1",
            "merkle_root_sha256": root_hash,
            "leaf_count": len(self.leaves),
            "artifacts": self.audit_log
        }
        with open(output_path, "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"Cryptographic provenance attestation exported: {root_hash}")

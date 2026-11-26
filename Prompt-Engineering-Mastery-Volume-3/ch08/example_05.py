"""
State Persistence Engine: Serializes active agent workflow snapshots
to durable database records and verifies cryptographic integrity on rehydration.
"""

import json
import time
import hashlib
from typing import Dict, Any, Optional


class DurableSessionStore:
    """Manages persistent session snapshots with cryptographic tamper detection."""

    def __init__(self, database_client: Any, secret_salt: str = "enterprise_secret_salt"):
        self.db = database_client
        self.salt = secret_salt

    def generate_checksum(self, snapshot_dict: Dict[str, Any]) -> str:
        """Computes deterministic SHA256 checksum over canonical JSON payload."""
        clean_copy = {k: v for k, v in snapshot_dict.items() if k != "cryptographic_checksum"}
        canonical_json = json.dumps(clean_copy, sort_keys=True)
        raw_str = f"{canonical_json}::{self.salt}"
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

    def persist_snapshot(
        self,
        session_id: str,
        workflow_version: str,
        current_state: str,
        accumulated_vars: Dict[str, Any],
        completed_transitions: list
    ) -> str:
        """Persists workflow state snapshot to durable storage."""
        snapshot = {
            "session_id": session_id,
            "workflow_definition_version": workflow_version,
            "current_state": current_state,
            "state_entered_timestamp": time.time(),
            "accumulated_context_variables": accumulated_vars,
            "completed_transitions": completed_transitions,
        }
        checksum = self.generate_checksum(snapshot)
        snapshot["cryptographic_checksum"] = checksum

        self.db.save_record(session_id, json.dumps(snapshot))
        return checksum

    def rehydrate_snapshot(self, session_id: str) -> Dict[str, Any]:
        """Loads and verifies snapshot integrity before returning to orchestrator."""
        raw_json = self.db.load_record(session_id)
        if not raw_json:
            raise KeyError(f"Session '{session_id}' not found.")

        snapshot = json.loads(raw_json)
        recorded_checksum = snapshot.get("cryptographic_checksum")
        expected_checksum = self.generate_checksum(snapshot)

        if recorded_checksum != expected_checksum:
            raise ValueError(
                f"CRITICAL_INTEGRITY_VIOLATION: Session snapshot '{session_id}' has been "
                f"tampered with or corrupted in storage."
            )

        return snapshot

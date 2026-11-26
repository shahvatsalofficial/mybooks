"""
Typed Handoff Contract Enforcer: Validates incoming and outgoing inter-agent
messages against strict JSON Schemas, blocking unvalidated conversational payloads.
"""

from typing import Dict, Any, Tuple, Optional
import json


class HandoffContractValidationError(Exception):
    """Raised when a worker emits an invalid handoff payload."""
    pass


class HandoffValidator:
    """Enforces strict schema adherence on inter-agent handoff contracts."""

    REQUIRED_CONTRACT_KEYS = {
        "correlation_id",
        "sender_id",
        "target_id",
        "objective",
        "payload",
    }

    @classmethod
    def validate_incoming_packet(cls, packet_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Verifies that an incoming handoff packet adheres to the universal standard."""
        missing = cls.REQUIRED_CONTRACT_KEYS - set(packet_data.keys())
        if missing:
            return False, f"Malformed contract: Missing mandatory keys {list(missing)}"

        if not isinstance(packet_data["payload"], dict):
            return False, "Contract payload must be a JSON object dictionary."

        return True, None

    @classmethod
    def validate_worker_output(
        cls,
        output_payload: Dict[str, Any],
        expected_schema: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Validates that a worker's return payload matches the supervisor's schema."""
        required_fields = expected_schema.get("required", [])
        for field_name in required_fields:
            if field_name not in output_payload:
                return False, f"Worker output missing mandatory field: '{field_name}'"

        return True, None

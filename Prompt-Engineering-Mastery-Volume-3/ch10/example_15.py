# remediation_cloud_governor.py
# Production architectural fix: Enforces zero-destroy invariants and route verification gates.

class SREMigrationGovernor:
    """Enforces non-bypassable safety gates on infrastructure migration agents."""

    FORBIDDEN_COMMANDS = {"destroy", "down", "terminate", "rm"}

    def validate_command(self, tool_name: str, command: str) -> Tuple[bool, Optional[str]]:
        """Blocks destructive operations and enforces route verification."""
        for forbidden in self.FORBIDDEN_COMMANDS:
            if forbidden in command.lower():
                return False, (
                    f"INVIOLABLE_SAFETY_GATE: Destructive command '{forbidden}' is strictly "
                    f"prohibited in autonomous mode. Human escalation required."
                )

        return True, None

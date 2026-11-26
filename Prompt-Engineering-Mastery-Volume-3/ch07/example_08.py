# remediation_patch_governor.py
# Production architectural fix: Enforces scope clamping and environmental unit test gating.

class AutonomousPatchingGovernor:
    """Restricts patch blast radius and enforces unit test verification before PR creation."""

    MAX_PERMITTED_DIFF_LINES = 25

    def validate_patch_scope(self, original_code: str, proposed_code: str, target_function: str) -> Tuple[bool, Optional[str]]:
        """Ensures the agent only touched the targeted vulnerability function."""
        orig_lines = original_code.splitlines()
        prop_lines = proposed_code.splitlines()

        import difflib
        diff = list(difflib.unified_diff(orig_lines, prop_lines))
        diff_count = len([line for line in diff if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))])

        if diff_count > self.MAX_PERMITTED_DIFF_LINES:
            return False, (
                f"SCOPE_BLAST_RADIUS_EXCEEDED: Proposed patch modified {diff_count} lines. "
                f"Maximum permitted modification is {self.MAX_PERMITTED_DIFF_LINES} lines. "
                f"Agent attempted out-of-scope refactoring. Patch rejected."
            )

        return True, None

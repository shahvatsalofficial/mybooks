# remediation_loan_fsm.py
# Production architectural fix: Enforces strict state adjacency and tool masking.

class LoanOriginationFSMGovernor:
    """Enforces non-bypassable adjacency graph and guard conditions on loan workflows."""

    LEGAL_TRANSITIONS = {
        "STAGE_IDENTITY_KYC": {"STAGE_CREDIT_UNDERWRITING", "STAGE_REJECTED"},
        "STAGE_CREDIT_UNDERWRITING": {"STAGE_COMPLIANCE_DISCLOSURE", "STAGE_REJECTED"},
        "STAGE_COMPLIANCE_DISCLOSURE": {"STAGE_ACH_DISBURSEMENT", "STAGE_CANCELLED"},
        "STAGE_ACH_DISBURSEMENT": {"STAGE_COMPLETED"},
    }

    def validate_transition_request(
        self,
        current_state: str,
        target_state: str,
        credit_score: Optional[int]
    ) -> Tuple[bool, Optional[str]]:
        """Blocks illegal jumps and evaluates hard financial invariants."""
        allowed_targets = self.LEGAL_TRANSITIONS.get(current_state, set())

        if target_state not in allowed_targets:
            return False, (
                f"CRITICAL_COMPLIANCE_VIOLATION: Attempted illegal jump from '{current_state}' "
                f"to '{target_state}'. Permitted transitions strictly: {list(allowed_targets)}. "
                f"Action blocked and reported to Risk."
            )

        # Invariant Check for Credit Underwriting
        if current_state == "STAGE_CREDIT_UNDERWRITING" and target_state == "STAGE_COMPLIANCE_DISCLOSURE":
            if credit_score is None or credit_score < 660:
                return False, (
                    f"GUARD_VETO: Credit score ({credit_score}) does not satisfy mandatory "
                    f"underwriting threshold of 660. Transition rejected."
                )

        return True, None

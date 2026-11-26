from pydantic import BaseModel, Field

class LoanUnderwritingApplication(BaseModel):
    application_id: str
    borrower_name: str
    total_debt_usd: float = Field(..., ge=0.0)
    total_equity_usd: float = Field(..., ge=1.0)
    requested_facility_usd: float = Field(..., ge=0.0)

class CreditDecisionRecord(BaseModel):
    application_id: str
    debt_to_equity_ratio: float
    llm_recommendation: str
    final_system_verdict: str  # APPROVED | REJECTED_HARD_POLICY_STOP
    audit_notes: str

class HardStopCreditFirewall:
    MAX_PERMISSIBLE_DEBT_TO_EQUITY = 2.50

    @classmethod
    def enforce_policy_boundary(
        cls,
        app: LoanUnderwritingApplication,
        llm_verdict_text: str
    ) -> CreditDecisionRecord:
        ratio = round(app.total_debt_usd / app.total_equity_usd, 3)

        # Inviolable deterministic hard stop
        if ratio > cls.MAX_PERMISSIBLE_DEBT_TO_EQUITY:
            return CreditDecisionRecord(
                application_id=app.application_id,
                debt_to_equity_ratio=ratio,
                llm_recommendation=llm_verdict_text,
                final_system_verdict="REJECTED_HARD_POLICY_STOP",
                audit_notes=(
                    f"Policy Hard-Stop: Debt-to-equity ({ratio}) exceeds statutory limit ({cls.MAX_PERMISSIBLE_DEBT_TO_EQUITY}). "
                    "Autonomous LLM recommendation overridden and suppressed."
                )
            )

        return CreditDecisionRecord(
            application_id=app.application_id,
            debt_to_equity_ratio=ratio,
            llm_recommendation=llm_verdict_text,
            final_system_verdict="APPROVED" if "APPROVE" in llm_verdict_text.upper() else "REJECTED",
            audit_notes="Underwriting within acceptable statutory variance."
        )

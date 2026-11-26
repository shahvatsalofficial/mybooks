class CreditRiskSignature(dspy.Signature):
    """Underwrite commercial borrower credit risk and assign tier."""
    financial_telemetry = dspy.InputField(desc="Quarterly balance sheet and cash flow metrics")
    debt_obligations = dspy.InputField(desc="Existing debt schedule and covenants")
    risk_assessment = dspy.OutputField(desc="Validated risk classification and capital reserve limit")

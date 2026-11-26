ALLOWED_REASONS = {"DUPLICATE_CHARGE", "SLA_BREACH", "BILLING_ERROR"}

def validate_credit_decision_safe(
    decision: dict[str, Any], inv: TicketInvariants
) -> dict[str, Any]:
    amount = float(decision.get("credit_usd", 0))
    currency = decision.get("currency")
    reason = decision.get("reason_code")
    if currency != "USD":
        return {"is_error": True, "message": "Only USD currency is supported."}
    if reason not in ALLOWED_REASONS:
        return {"is_error": True, "message": f"reason_code must be one of {sorted(ALLOWED_REASONS)}."}
    if amount <= 0 or amount > inv.max_autonomous_credit_usd:
        return {"is_error": True, "message": f"credit_usd must be in (0, {inv.max_autonomous_credit_usd}]."}
    return {"is_error": False, "validated": True}

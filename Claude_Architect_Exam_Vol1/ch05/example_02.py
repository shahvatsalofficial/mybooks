def issue_credit(args: dict[str, Any]) -> dict[str, Any]:
    invoice_id = str(args.get("invoice_id", ""))
    amount = float(args.get("amount_usd", 0))
    if not INVOICE_RE.match(invoice_id):
        raise ValueError("Invalid invoice_id. Expected ^INV-[0-9]{5}$.")
    if amount <= 0:
        raise ValueError("amount_usd must be greater than 0.")
    if amount > 500.0:
        # Caller catches PolicyError or returns POLICY_BLOCKED via isError: true
        return {
            "is_error": True,
            "error_code": "POLICY_BLOCKED",
            "message": f"Credit ${amount:.2f} exceeds the $500.00 autonomous limit.",
            "recovery_hint": "Call human_billing_review instead of retrying billing_issue_credit.",
        }
    return {"invoice_id": invoice_id, "credited_usd": amount, "status": "applied"}

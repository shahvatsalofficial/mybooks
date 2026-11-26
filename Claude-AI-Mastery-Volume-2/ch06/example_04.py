@mcp.prompt()
def analyze_counterparty_credit_risk(counterparty_id: str, reporting_currency: str = "USD") -> str:
    """Generates an executive risk audit prompt targeting counterparty credit exposures."""
    return f"""You are the Chief Enterprise Risk Officer.
Conduct a rigorous credit and solvency evaluation for counterparty '{counterparty_id}'.
All monetary assessments must be reported in '{reporting_currency}'.
Follow this execution protocol:
1. Call 'assess_single_asset_risk' for all active derivative contracts.
2. Read resource 'market://macro/indices' to evaluate interest rate and volatility trends.
3. Quantify 30-day default probability under a 200 bps market shock scenario.
Provide your final findings as a structured executive audit report."""

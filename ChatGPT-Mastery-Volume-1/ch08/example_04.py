"""
Architectural Drill 2: 5-Stage DuPont ROE Calculator & Anomaly Detector
"""

from typing import Dict, Any, List

def compute_dupont_5stage(metrics: Dict[str, float]) -> Dict[str, Any]:
    net_income = metrics["net_income"]
    ebt = metrics["ebt"]
    ebit = metrics["ebit"]
    revenue = metrics["revenue"]
    assets = metrics["total_assets"]
    equity = metrics["stockholders_equity"]

    # Assertion of valid denominators
    for key, val in [("ebt", ebt), ("ebit", ebit), ("revenue", revenue), ("assets", assets), ("equity", equity)]:
        if val <= 0:
            raise ValueError(f"Invalid accounting value for {key}: {val}. Must be strictly positive.")

    tax_burden = net_income / ebt
    interest_burden = ebt / ebit
    operating_margin = ebit / revenue
    asset_turnover = revenue / assets
    equity_multiplier = assets / equity
    roe = tax_burden * interest_burden * operating_margin * asset_turnover * equity_multiplier

    # Anomaly Detection Alerts
    alerts: List[str] = []
    if equity_multiplier > 4.0:
        alerts.append(f"HIGH_LEVERAGE_RISK: Financial leverage ({equity_multiplier:.2f}x) exceeds safe threshold (4.0x).")
    if interest_burden < 0.65:
        alerts.append(f"DEBT_SERVICE_HAZARD: Interest burden ({interest_burden:.2f}) indicates severe earnings drag from debt obligations.")
    if operating_margin < 0.05:
        alerts.append(f"MARGIN_COMPRESSION: Operating margin ({operating_margin*100:.1f}%) indicates minimal operational pricing power.")

    return {
        "tax_burden": round(tax_burden, 4),
        "interest_burden": round(interest_burden, 4),
        "operating_margin": round(operating_margin, 4),
        "asset_turnover": round(asset_turnover, 4),
        "equity_multiplier": round(equity_multiplier, 4),
        "computed_roe": round(roe, 4),
        "alerts": alerts,
        "is_healthy": len(alerts) == 0
    }

# Verification Test
healthy_firm = {
    "net_income": 20000.0, "ebt": 25000.0, "ebit": 30000.0,
    "revenue": 100000.0, "total_assets": 80000.0, "stockholders_equity": 40000.0
}
res = compute_dupont_5stage(healthy_firm)
assert res["is_healthy"] == True
assert res["computed_roe"] == 0.50

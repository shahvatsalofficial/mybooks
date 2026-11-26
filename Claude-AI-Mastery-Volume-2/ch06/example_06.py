"""
Recipe 06.1: Enterprise Financial Risk FastMCP Server
Author: Vatsal Shah (Opportunity4u Press)
License: Apache-2.0
"""

import os
import json
import logging
import math
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from mcp.server.fastmcp import FastMCP
import anyio

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("FinRiskMCP")

# Tune AnyIO thread limiter for heavy analytical operations
limiter = anyio.to_thread.current_default_thread_limiter()
limiter.total_tokens = 100

# Initialize FastMCP Server
mcp = FastMCP("enterprise-financial-risk", dependencies=["httpx", "pydantic", "numpy"])

# --- Typed Domain Models ---
class RiskAssessmentInput(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol (e.g. AAPL, NVDA, MSFT)", min_length=1, max_length=10)
    position_size_usd: float = Field(..., description="Total portfolio market value in USD", gt=0.0)
    confidence_level: float = Field(default=0.95, description="VaR statistical confidence interval (0.90, 0.95, 0.99)")
    time_horizon_days: int = Field(default=1, description="Holding period in trading days", ge=1, le=30)

    @field_validator("ticker")
    @classmethod
    def clean_ticker(cls, v: str) -> str:
        return v.strip().upper()

class PositionItem(BaseModel):
    symbol: str = Field(..., description="Equity ticker")
    shares: int = Field(..., gt=0, description="Quantity of shares held")
    current_price: float = Field(..., gt=0.0, description="Current market price per share")
    asset_class: str = Field(default="EQUITY", description="Asset classification: EQUITY, FIXED_INCOME, CRYPTO")

class PortfolioRebalanceInput(BaseModel):
    portfolio_id: str = Field(..., description="Client portfolio account identifier")
    positions: List[PositionItem] = Field(..., description="List of active holdings")
    target_cash_percent: float = Field(default=0.15, description="Target cash allocation ratio (0.0 to 1.0)", ge=0.0, le=1.0)

# --- 1. Production Tools with Pydantic Validation ---
@mcp.tool()
async def assess_single_asset_risk(params: RiskAssessmentInput) -> str:
    """Calculates Parametric Value-at-Risk (VaR) and volatility exposure for an equity position."""
    logger.info(f"Assessing risk for {params.ticker} with exposure ${params.position_size_usd:,.2f}")
    
    # Quantitative Risk Lookup (Simulated High-Performance Model)
    volatility_map = {"NVDA": 0.48, "TSLA": 0.55, "AAPL": 0.22, "MSFT": 0.20, "GOOGL": 0.24}
    annual_vol = volatility_map.get(params.ticker, 0.30)
    daily_vol = annual_vol / math.sqrt(252)

    # Z-Score Lookup for parametric VaR
    z_scores = {0.90: 1.645, 0.95: 1.960, 0.99: 2.576}
    z = z_scores.get(params.confidence_level, 1.960)

    # Parametric VaR = Position * Daily_Vol * Z * sqrt(Time_Horizon)
    var_amount = params.position_size_usd * daily_vol * z * math.sqrt(params.time_horizon_days)

    result = {
        "ticker": params.ticker,
        "position_usd": params.position_size_usd,
        "annualized_volatility": round(annual_vol, 4),
        "daily_volatility": round(daily_vol, 4),
        "confidence_level": params.confidence_level,
        "time_horizon_days": params.time_horizon_days,
        "value_at_risk_usd": round(var_amount, 2),
        "risk_rating": "CRITICAL" if var_amount > 50000 else "ELEVATED" if var_amount > 15000 else "STANDARD",
        "action_required": var_amount > 50000
    }
    return json.dumps(result, indent=2)

def _compute_rebalance_sync(portfolio_id: str, positions: List[PositionItem], target_cash_ratio: float) -> Dict[str, Any]:
    """CPU-bound portfolio matrix optimization executing in dedicated worker thread."""
    total_val = sum(p.shares * p.current_price for p in positions)
    target_cash_usd = total_val * target_cash_ratio
    
    # Sort positions by highest exposure to recommend targeted liquidations
    sorted_positions = sorted(positions, key=lambda p: p.shares * p.current_price, reverse=True)
    accumulated_cash = 0.0
    liquidation_schedule = []

    for pos in sorted_positions:
        if accumulated_cash >= target_cash_usd:
            break
        pos_val = pos.shares * pos.current_price
        shares_to_sell = min(pos.shares, math.ceil((target_cash_usd - accumulated_cash) / pos.current_price))
        sale_proceeds = shares_to_sell * pos.current_price
        accumulated_cash += sale_proceeds
        liquidation_schedule.append({
            "symbol": pos.symbol,
            "shares_to_liquidate": shares_to_sell,
            "estimated_proceeds_usd": round(sale_proceeds, 2),
            "remaining_shares": pos.shares - shares_to_sell
        })

    return {
        "portfolio_id": portfolio_id,
        "gross_portfolio_value_usd": round(total_val, 2),
        "target_cash_reserve_usd": round(target_cash_usd, 2),
        "generated_cash_usd": round(accumulated_cash, 2),
        "recommended_orders": liquidation_schedule,
        "status": "FEASIBLE" if accumulated_cash >= target_cash_usd else "INSUFFICIENT_LIQUIDITY"
    }

@mcp.tool()
async def batch_portfolio_rebalance(params: PortfolioRebalanceInput) -> str:
    """Calculates required equity liquidations to achieve target cash reserve ratios.
    Executes in an AnyIO worker thread pool to prevent blocking the async event loop.
    """
    logger.info(f"Scheduling portfolio rebalance for {params.portfolio_id} across {len(params.positions)} holdings")
    # Offload blocking computation to thread pool
    result = await anyio.to_thread.run_sync(
        _compute_rebalance_sync,
        params.portfolio_id,
        params.positions,
        params.target_cash_percent
    )
    return json.dumps(result, indent=2)

# --- 2. Dynamic Resources ---
@mcp.resource("market://macro/benchmarks")
def get_macro_market_indices() -> str:
    """Provides real-time index benchmarks, yields, and implied volatility indicators."""
    return json.dumps({
        "timestamp": "2026-10-01T15:30:00Z",
        "SP500": {"index": 5854.20, "change_pct": 0.42},
        "NASDAQ100": {"index": 20450.80, "change_pct": 0.65},
        "CBOE_VIX": {"index": 14.10, "change_pct": -3.20},
        "US_TREASURY_10Y": {"yield_pct": 4.08, "change_bps": -2.5}
    }, indent=2)

@mcp.resource("market://tenants/{tenant_id}/risk_limits")
async def get_tenant_risk_limits(tenant_id: str) -> str:
    """Returns organizational risk limits and portfolio mandates for a designated enterprise tenant."""
    return json.dumps({
        "tenant_id": tenant_id,
        "max_single_stock_exposure_pct": 12.5,
        "max_portfolio_daily_var_usd": 150000.0,
        "forbidden_sectors": ["TOBACCO", "WEAPONS"],
        "mandatory_esg_score_floor": 65.0
    }, indent=2)

# --- 3. Cognitive Prompt Templates ---
@mcp.prompt()
def audit_client_portfolio_mandate(client_id: str, compliance_framework: str = "SEC_RULE_15C3") -> str:
    """Generates an autonomous compliance audit prompt targeting client investment mandates."""
    return f"""You are the Chief Enterprise Risk Officer. 
Conduct a formal compliance review of client account '{client_id}' under regulatory standard '{compliance_framework}'.
1. Inspect all active equity exposures using 'assess_single_asset_risk'.
2. Verify leverage and portfolio liquidity ratios against market macro index benchmarks from 'market://macro/benchmarks'.
3. Check organizational exposure ceilings against 'market://tenants/{client_id}/risk_limits'.
4. If single-asset VaR breaches compliance ceilings, run 'batch_portfolio_rebalance' to restore balance.
Deliver a structured audit summary detailing all discovered infractions and remediation steps."""

if __name__ == "__main__":
    # Standard input/output transport for local desktop or CLI integration
    mcp.run(transport="stdio")

# case_studies/cs01_trading_floor_agent.py
"""
Case Study 01: Multi-Agent Trading Floor with SLA Guardrails & Circuit Breakers.
Author: Vatsal Shah — The Agentic Frontier Vol 2
"""

import time
import logging
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, field_validator
from langgraph.graph import StateGraph, END

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TradingFloorAgent")

# ============================================================================
# 1. DOMAIN SCHEMAS & PROTOCOL DEFINITIONS
# ============================================================================

class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"

class OrderCandidate(BaseModel):
    cl_ord_id: str = Field(..., description="Unique client order tracking ID")
    symbol: str = Field(..., description="Ticker symbol (e.g. AAPL, NVDA)")
    side: OrderSide
    order_type: OrderType
    quantity: int = Field(..., gt=0, description="Order quantity in units")
    target_price: float = Field(..., gt=0.0, description="Limit target price")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    timestamp_ns: int = Field(default_factory=time.time_ns)

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        v_upper = v.upper().strip()
        if not v_upper.isalpha() or len(v_upper) > 5:
            raise ValueError(f"Invalid trading symbol format: {v}")
        return v_upper

class RiskEvaluationResult(BaseModel):
    approved: bool
    risk_score: float
    rejection_reason: Optional[str] = None
    capital_committed: float

class FIXOrderPayload(BaseModel):
    msg_type: str = "D"  # New Order Single
    cl_ord_id: str
    symbol: str
    side: str
    transact_time: str
    order_qty: int
    ord_type: str
    price: float
    handl_inst: str = "1"  # Automated execution

# ============================================================================
# 2. LANGGRAPH STATE DEFINITION
# ============================================================================

class TradingState(BaseModel):
    market_snapshot: Dict[str, Any]
    candidate: Optional[OrderCandidate] = None
    risk_result: Optional[RiskEvaluationResult] = None
    fix_payload: Optional[FIXOrderPayload] = None
    execution_status: str = "INITIALIZED"
    error_logs: List[str] = Field(default_factory=list)
    start_time_ns: int = Field(default_factory=time.time_ns)
    elapsed_ms: float = 0.0

# ============================================================================
# 3. MULTI-AGENT GRAPH NODES
# ============================================================================

def analyst_node(state: TradingState) -> Dict[str, Any]:
    """
    Analyst Agent: Processes market snapshot and generates order candidate.
    """
    logger.info(" [Analyst Agent] Evaluating market order book signals...")
    snapshot = state.market_snapshot
    symbol = snapshot.get("symbol", "NVDA")
    bid_price = snapshot.get("bid", 120.50)
    ask_price = snapshot.get("ask", 120.55)
    momentum = snapshot.get("momentum_score", 0.85)

    if momentum > 0.70:
        candidate = OrderCandidate(
            cl_ord_id=f"ORD-{time.time_ns()}",
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1000,
            target_price=ask_price,
            confidence_score=momentum
        )
        logger.info(f" [Analyst Agent] Generated candidate: BUY {candidate.quantity} {candidate.symbol} @ ${candidate.target_price}")
        return {"candidate": candidate, "execution_status": "ANALYSIS_COMPLETE"}
    else:
        logger.info("⏸️ [Analyst Agent] Signals below threshold. No order generated.")
        return {"execution_status": "NO_ACTION"}

def risk_node(state: TradingState) -> Dict[str, Any]:
    """
    Risk Assessment Agent: Evaluates candidate against position limits & VaR bounds.
    Includes deterministic circuit breaker.
    """
    logger.info("️ [Risk Agent] Auditing order candidate against compliance rules...")
    candidate = state.candidate
    if not candidate:
        return {"execution_status": "RISK_REJECTED", "error_logs": ["No candidate provided"]}

    capital_required = candidate.quantity * candidate.target_price
    MAX_CAPITAL_PER_ORDER = 250000.0  # $250k limit

    if capital_required > MAX_CAPITAL_PER_ORDER:
        reason = f"Capital required (${capital_required:,.2f}) exceeds max limit (${MAX_CAPITAL_PER_ORDER:,.2f})"
        logger.warning(f" [Risk Agent] REJECTED: {reason}")
        return {
            "risk_result": RiskEvaluationResult(
                approved=False,
                risk_score=0.95,
                rejection_reason=reason,
                capital_committed=0.0
            ),
            "execution_status": "RISK_REJECTED"
        }

    # Approved
    logger.info(f" [Risk Agent] APPROVED: Committed ${capital_required:,.2f} capital.")
    return {
        "risk_result": RiskEvaluationResult(
            approved=True,
            risk_score=0.12,
            capital_committed=capital_required
        ),
        "execution_status": "RISK_APPROVED"
    }

def execution_node(state: TradingState) -> Dict[str, Any]:
    """
    Execution Agent: Translates approved candidate into FIX 4.4 protocol payload.
    Applies microsecond-level Pydantic schema validation.
    """
    logger.info("⚡ [Execution Agent] Converting order candidate to FIX payload...")
    candidate = state.candidate
    risk = state.risk_result

    if not candidate or not risk or not risk.approved:
        return {"execution_status": "EXECUTION_ABORTED"}

    # Translate to FIX Payload
    fix = FIXOrderPayload(
        cl_ord_id=candidate.cl_ord_id,
        symbol=candidate.symbol,
        side="1" if candidate.side == OrderSide.BUY else "2",
        transact_time=time.strftime("%Y%m%d-%H:%M:%S.000"),
        order_qty=candidate.quantity,
        ord_type="2" if candidate.order_type == OrderType.LIMIT else "1",
        price=candidate.target_price
    )

    elapsed = (time.time_ns() - state.start_time_ns) / 1e6
    logger.info(f" [Execution Agent] FIX Order {fix.cl_ord_id} dispatched in {elapsed:.2f}ms!")
    return {
        "fix_payload": fix,
        "execution_status": "DISPATCHED",
        "elapsed_ms": elapsed
    }

# ============================================================================
# 4. CONDITIONAL ROUTING & GRAPH COMPILATION
# ============================================================================

def route_after_analyst(state: TradingState) -> str:
    if state.execution_status == "ANALYSIS_COMPLETE":
        return "risk_node"
    return END

def route_after_risk(state: TradingState) -> str:
    if state.execution_status == "RISK_APPROVED":
        return "execution_node"
    return END

def build_trading_graph():
    builder = StateGraph(TradingState)
    builder.add_node("analyst_node", analyst_node)
    builder.add_node("risk_node", risk_node)
    builder.add_node("execution_node", execution_node)

    builder.set_entry_point("analyst_node")
    builder.add_conditional_edges("analyst_node", route_after_analyst, ["risk_node", END])
    builder.add_conditional_edges("risk_node", route_after_risk, ["execution_node", END])
    builder.add_edge("execution_node", END)

    return builder.compile()

# Example Execution Test
if __name__ == "__main__":
    graph = build_trading_graph()
    sample_snapshot = {
        "symbol": "NVDA",
        "bid": 120.50,
        "ask": 120.55,
        "momentum_score": 0.88
    }
    init_state = TradingState(market_snapshot=sample_snapshot)
    final_state = graph.invoke(init_state)
    print(f"\nFinal Status: {final_state['execution_status']}")
    print(f"Total Latency: {final_state['elapsed_ms']:.2f} ms")

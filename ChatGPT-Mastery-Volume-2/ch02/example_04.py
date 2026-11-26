"""
Deterministic State Machine Tool Guard
Enforces chronological execution order across multi-tool agent workflows.
"""
from enum import Enum
from typing import Set, Dict

class AgentState(str, Enum):
    INIT = "INIT"
    IDENTITY_VERIFIED = "IDENTITY_VERIFIED"
    CART_STAGED = "CART_STAGED"
    PAYMENT_AUTHORIZED = "PAYMENT_AUTHORIZED"
    ORDER_COMPLETED = "ORDER_COMPLETED"

class ToolStateGuard:
    # State transitions: Current State -> Set of Allowable Tools
    ALLOWED_TOOLS_BY_STATE: Dict[AgentState, Set[str]] = {
        AgentState.INIT: {"verify_customer_identity", "fetch_catalog_items"},
        AgentState.IDENTITY_VERIFIED: {"create_cart_order", "apply_discount_code"},
        AgentState.CART_STAGED: {"authorize_credit_payment", "modify_cart_items"},
        AgentState.PAYMENT_AUTHORIZED: {"commit_final_order"},
        AgentState.ORDER_COMPLETED: {"generate_invoice_pdf", "send_confirmation_email"}
    }

    def __init__(self):
        self.current_state = AgentState.INIT

    def validate_tool_invocation(self, tool_name: str) -> bool:
        allowed = self.ALLOWED_TOOLS_BY_STATE.get(self.current_state, set())
        if tool_name not in allowed:
            raise PermissionError(
                f"ILLEGAL TOOL SEQUENCE: Tool '{tool_name}' cannot be invoked while in state '{self.current_state.value}'. "
                f"Permitted tools: {list(allowed)}"
            )
        return True

    def transition(self, new_state: AgentState):
        logger.info(f"Agent state transitioned: {self.current_state.value} -> {new_state.value}")
        self.current_state = new_state

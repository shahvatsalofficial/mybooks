class AgentState(str, Enum):
    AUTHENTICATE = "authenticate"
    FETCH_ORDER = "fetch_order"
    EVALUATE_POLICY = "evaluate_policy"
    EXECUTE_REFUND = "execute_refund"
    TERMINATE = "terminate"

class FSMAgent:
    def __init__(self, user_id: str, order_id: str):
        self.user_id = user_id
        self.order_id = order_id
        self.current_state = AgentState.AUTHENTICATE
        self.audit_log: List[str] = []
        self.refund_approved = False

    def transition(self, next_state: AgentState, reason: str):
        self.audit_log.append(f"{self.current_state.value} -> {next_state.value} | Reason: {reason}")
        self.current_state = next_state

    def step(self):
        if self.current_state == AgentState.AUTHENTICATE:
            if self.user_id.startswith("USR-"):
                self.transition(AgentState.FETCH_ORDER, "User credentials verified in directory.")
            else:
                self.transition(AgentState.TERMINATE, "Authentication failed: Invalid user ID format.")

        elif self.current_state == AgentState.FETCH_ORDER:
            if self.order_id.startswith("ORD-"):
                self.transition(AgentState.EVALUATE_POLICY, "Order metadata retrieved successfully.")
            else:
                self.transition(AgentState.TERMINATE, "Order not found in operational database.")

        elif self.current_state == AgentState.EVALUATE_POLICY:
            self.refund_approved = True
            self.transition(AgentState.EXECUTE_REFUND, "Order meets all return policy guidelines.")

        elif self.current_state == AgentState.EXECUTE_REFUND:
            self.transition(AgentState.TERMINATE, f"Refund TX-REF-{self.order_id} disbursed.")

    def run_until_complete(self) -> List[str]:
        while self.current_state != AgentState.TERMINATE:
            self.step()
        return self.audit_log

# Verification
fsm = FSMAgent(user_id="USR-4902", order_id="ORD-7712")
logs = fsm.run_until_complete()
print("FSM State Audit Trail:")
for l in logs:
    print(f"  {l}")

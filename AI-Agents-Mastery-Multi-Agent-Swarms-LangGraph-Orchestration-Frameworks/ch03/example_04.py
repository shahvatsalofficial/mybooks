# Parent Node Wrappers for Child Subgraphs
def billing_adapter_node(state: GlobalParentState) -> Dict[str, Any]:
    print("[PARENT GRAPH] Routing task into Billing Subgraph...")
    # 1. Map Parent State to Child Input Contract
    child_input: BillingSubgraphState = {
        "invoice_id": "INV-2026-9912",
        "customer_tier": state["customer_tier"],
        "billing_logs": [],
        "refund_amount_cents": 0,
        "refund_authorized": False,
        "billing_summary": ""
    }
    
    # 2. Execute Child Subgraph Run
    child_output = billing_subgraph.invoke(child_input)
    
    # 3. Map Child Output back to Parent Global State Contract
    return {
        "messages": [f"[Billing Specialist]: {child_output['billing_summary']}"],
        "resolution_status": "resolved" if child_output["refund_authorized"] else "escalated",
        "final_resolution_summary": child_output["billing_summary"]
    }

def tech_adapter_node(state: GlobalParentState) -> Dict[str, Any]:
    print("[PARENT GRAPH] Routing task into Tech Support Subgraph...")
    child_input: TechSupportSubgraphState = {
        "service_name": "payment-gateway-svc",
        "error_code": "ERR_503_DOWN",
        "diagnostic_traces": [],
        "remediation_action": "",
        "tech_summary": ""
    }
    
    child_output = tech_subgraph.invoke(child_input)
    
    return {
        "messages": [f"[Tech Specialist]: {child_output['tech_summary']}"],
        "resolution_status": "resolved",
        "final_resolution_summary": child_output["tech_summary"]
    }

def triage_router(state: GlobalParentState) -> Literal["billing_agent", "tech_agent"]:
    """Inspects parent messages to route to correct specialist subgraph."""
    last_msg = state["messages"][-1].lower() if state["messages"] else ""
    if "refund" in last_msg or "invoice" in last_msg or "charge" in last_msg:
        print("[PARENT TRIAGE] Classified intent: BILLING.")
        return "billing_agent"
    else:
        print("[PARENT TRIAGE] Classified intent: TECHNICAL.")
        return "tech_agent"

# --- Build and Compile Parent StateGraph ---
parent_builder = StateGraph(GlobalParentState)
parent_builder.add_node("billing_agent", billing_adapter_node)
parent_builder.add_node("tech_agent", tech_adapter_node)

parent_builder.add_conditional_edges(
    START,
    triage_router,
    {
        "billing_agent": "billing_agent",
        "tech_agent": "tech_agent"
    }
)
parent_builder.add_edge("billing_agent", END)
parent_builder.add_edge("tech_agent", END)

parent_app = parent_builder.compile()

from langgraph.graph import StateGraph, START, END

# --- Billing Subgraph Nodes ---
def retrieve_invoice_node(state: BillingSubgraphState) -> Dict[str, Any]:
    inv = state["invoice_id"]
    print(f"  [BILLING SUBGRAPH: Retrieve] Fetching invoice {inv} from Stripe API...")
    return {
        "billing_logs": [f"Retrieved Stripe invoice {inv}: Total $45.00, Status: Charged"],
        "refund_amount_cents": 4500
    }

def authorize_refund_node(state: BillingSubgraphState) -> Dict[str, Any]:
    tier = state["customer_tier"]
    amt = state["refund_amount_cents"]
    print(f"  [BILLING SUBGRAPH: Authorize] Evaluating refund for {tier} tier (Amount: ${amt/100:.2f})...")
    
    # Policy: Enterprise tier auto-approved; standard requires manual check if > $20
    is_auto_approved = (tier == "enterprise") or (amt <= 2000)
    status_str = "AUTHORIZED" if is_auto_approved else "PENDING_MANUAL_REVIEW"
    summary = f"Billing Action: Refund of ${amt/100:.2f} {status_str} for invoice {state['invoice_id']}."
    
    return {
        "refund_authorized": is_auto_approved,
        "billing_summary": summary
    }

# --- Compile Billing Subgraph ---
billing_builder = StateGraph(BillingSubgraphState)
billing_builder.add_node("retrieve_invoice", retrieve_invoice_node)
billing_builder.add_node("authorize_refund", authorize_refund_node)
billing_builder.add_edge(START, "retrieve_invoice")
billing_builder.add_edge("retrieve_invoice", "authorize_refund")
billing_builder.add_edge("authorize_refund", END)

billing_subgraph = billing_builder.compile()

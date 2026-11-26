# --- Tech Support Subgraph Nodes ---
def diagnose_logs_node(state: TechSupportSubgraphState) -> Dict[str, Any]:
    svc = state["service_name"]
    code = state["error_code"]
    print(f"  [TECH SUBGRAPH: Diagnose] Scanning Datadog APM logs for {svc} (Error: {code})...")
    trace = f"Found NullPointerException in auth middleware for {svc} under error {code}."
    return {"diagnostic_traces": [trace]}

def execute_remediation_node(state: TechSupportSubgraphState) -> Dict[str, Any]:
    svc = state["service_name"]
    print(f"  [TECH SUBGRAPH: Remediate] Cycling pod replica for {svc}...")
    summary = f"Tech Action: Pod restart dispatched for service '{svc}'. Health check returned HTTP 200."
    return {
        "remediation_action": "RESTART_POD",
        "tech_summary": summary
    }

# --- Compile Tech Support Subgraph ---
tech_builder = StateGraph(TechSupportSubgraphState)
tech_builder.add_node("diagnose_logs", diagnose_logs_node)
tech_builder.add_node("execute_remediation", execute_remediation_node)
tech_builder.add_edge(START, "diagnose_logs")
tech_builder.add_edge("diagnose_logs", "execute_remediation")
tech_builder.add_edge("execute_remediation", END)

tech_subgraph = tech_builder.compile()

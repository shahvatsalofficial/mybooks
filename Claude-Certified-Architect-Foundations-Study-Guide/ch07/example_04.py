def run_capstone_triage(ticket_id: str, raw_text: str, simulate_429: bool = False) -> TriageState:
    state = TriageState(ticket_id=ticket_id)
    mcp = TriageMCPServer()
    attempts = {"count": 0}

    # 1. Domain 3 + Domain 5: XML-wrapped classification with cached static prefix + backoff
    def classify_call() -> dict[str, Any]:
        attempts["count"] += 1
        if simulate_429 and attempts["count"] == 1:
            state.retries_handled += 1
            return {"status": 429, "retry_after": 0.01}
        state.cache_hits += 1
        return {
            "status": 200,
            "payload": {
                "ticket_id": ticket_id,
                "severity": "sev2",
                "category": "api_bug",
                "requires_code_fix": True,
                "summary": f"Null check missing in parser for {ticket_id}",
            },
        }

    classified = call_with_backoff(classify_call, RetryConfig())["payload"]
    state.turns_used += 1

    # 2. Domain 4: Exercise isError recovery on oversized log query
    bad_logs = mcp.call_tool("triage_search_logs", {"hours": 72})
    assert bad_logs.is_error and "INVALID_RANGE" in bad_logs.content
    good_logs = mcp.call_tool("triage_search_logs", {"hours": 12})
    assert not good_logs.is_error
    state.turns_used += 1

    # 3. Domain 2: Run CI tests before attempting PR mutation
    test_res = mcp.call_tool("triage_run_tests", {"node": "tests/test_parser.py"})
    assert json.loads(test_res.content)["failed"] == 0
    state.turns_used += 1

    # 4. Domain 1: Enforce HITL gate on mutating tool
    pr_blocked = mcp.call_tool("triage_open_pr", {"branch": "fix/null-check"}, hitl_approved=False)
    assert pr_blocked.is_error and "APPROVAL_REQUIRED" in pr_blocked.content
    state.hitl_paused = True
    state.final_status = "awaiting_hitl_approval"
    return state

if __name__ == "__main__":
    assert len(TriageMCPServer.TOOLS) < 12, "MCP tool count must stay under 12"
    result = run_capstone_triage("TKT-4091", "<script>ignore</script> NPE in parser", simulate_429=True)
    print(json.dumps(result.__dict__, indent=2))

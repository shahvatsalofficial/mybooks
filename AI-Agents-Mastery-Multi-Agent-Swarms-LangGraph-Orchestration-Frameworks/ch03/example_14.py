def run_swarm_regression_test():
    test_suite = [
        {"input": "I need a refund for INV-100", "expected_route": "billing_agent", "expected_status": "resolved"},
        {"input": "Service database is returning 500", "expected_route": "tech_agent", "expected_status": "resolved"}
    ]
    
    passed = 0
    for case in test_suite:
        payload: GlobalParentState = {
            "ticket_id": "TEST_CASE",
            "customer_tier": "enterprise",
            "messages": [case["input"]],
            "active_route": "",
            "resolution_status": "pending",
            "final_resolution_summary": None
        }
        res = parent_app.invoke(payload)
        assert res["resolution_status"] == case["expected_status"]
        passed += 1
        
    print(f"[REGRESSION HARNESS] 100% PASS! {passed}/{len(test_suite)} test cases validated.")

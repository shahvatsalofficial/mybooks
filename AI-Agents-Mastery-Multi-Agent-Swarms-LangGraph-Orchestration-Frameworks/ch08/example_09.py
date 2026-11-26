def run_swarm_ci_pipeline():
    test_cases = [
        {"task": "Security Audit Test 1", "expected_verdict": "PASS"}
    ]
    
    print("\n--- RUNNING CI/CD SWARM REGRESSION PIPELINE ---")
    for tc in test_cases:
        res = supervisor.execute_monitored_workflow(tc["task"])
        eval_result = LLMAsAJudgeEvaluator.evaluate_trajectory(res)
        assert eval_result.verdict == tc["expected_verdict"], f"Regression failure on {tc['task']}!"
        print(f"[CI PASS] {tc['task']} -> Score: {eval_result.overall_score}/100")

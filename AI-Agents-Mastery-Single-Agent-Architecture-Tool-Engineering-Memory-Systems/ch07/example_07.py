@dataclass
class GoldenTestCase:
    test_id: str
    prompt: str
    expected_tool: str
    forbidden_tokens: List[str]

class RegressionTestHarness:
    def __init__(self, test_cases: List[GoldenTestCase]):
        self.tests = test_cases

    def run_tests(self, agent_fn: Callable[[str], Tuple[str, str]]) -> Dict[str, Any]:
        passed = 0
        failures = []
        
        for t in self.tests:
            tool_called, final_answer = agent_fn(t.prompt)
            tool_ok = (tool_called == t.expected_tool)
            forbidden_clean = not any(tok in final_answer for tok in t.forbidden_tokens)
            
            if tool_ok and forbidden_clean:
                passed += 1
            else:
                failures.append({"test_id": t.test_id, "tool_ok": tool_ok, "forbidden_clean": forbidden_clean})

        return {
            "total": len(self.tests),
            "passed": passed,
            "pass_rate": round(passed / len(self.tests), 2),
            "failures": failures
        }

# Verification
test_suite = [
    GoldenTestCase("T1", "Lookup balance", "check_balance", ["INTERNAL_ERROR"]),
    GoldenTestCase("T2", "Transfer funds", "transfer_funds", ["EXCEPTION"])
]

def mock_agent(prompt: str):
    return ("check_balance", "Balance is $100.") if "balance" in prompt else ("transfer_funds", "Done.")

harness = RegressionTestHarness(test_suite)
print("Regression Test Pass Rate:", harness.run_tests(mock_agent)["pass_rate"] * 100, "%")

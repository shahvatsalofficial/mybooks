@dataclass
class BenchmarkScenario:
    scenario_id: str
    user_goal: str
    expected_tools: List[str]
    max_steps: int

class AgentBenchRunner:
    def __init__(self, scenarios: List[BenchmarkScenario], agent_runner_fn: Callable[[str], List[RecordedToolCall]]):
        self.scenarios = scenarios
        self.agent_runner = agent_runner_fn

    def run_benchmark(self) -> Dict[str, Any]:
        passed_count = 0
        total_steps = 0
        scenario_results = []

        for sc in self.scenarios:
            actual_calls = self.agent_runner(sc.user_goal)
            total_steps += len(actual_calls)
            
            # Verify all expected tools were executed within step budget
            actual_tool_names = set(c.tool_name for c in actual_calls)
            expected_met = all(t in actual_tool_names for t in sc.expected_tools)
            budget_met = len(actual_calls) <= sc.max_steps
            
            success = expected_met and budget_met
            if success:
                passed_count += 1
                
            scenario_results.append({
                "scenario_id": sc.scenario_id,
                "success": success,
                "step_count": len(actual_calls)
            })

        total_scenarios = len(self.scenarios)
        return {
            "total_scenarios": total_scenarios,
            "passed_scenarios": passed_count,
            "task_success_rate": round(passed_count / max(1, total_scenarios), 4),
            "average_steps_to_convergence": round(total_steps / max(1, total_scenarios), 2),
            "results": scenario_results
        }

# Verification
test_suite = [
    BenchmarkScenario("SCENARIO_01", "Reset password for user USR-10", ["lookup_user", "send_reset_email"], max_steps=3),
    BenchmarkScenario("SCENARIO_02", "Audit database index health", ["get_db_metrics", "check_slow_queries"], max_steps=4)
]

def mock_agent_runner(goal: str) -> List[RecordedToolCall]:
    if "password" in goal:
        return [RecordedToolCall("lookup_user", {}, 1), RecordedToolCall("send_reset_email", {}, 2)]
    return [RecordedToolCall("get_db_metrics", {}, 1), RecordedToolCall("check_slow_queries", {}, 2)]

runner = AgentBenchRunner(scenarios=test_suite, agent_runner_fn=mock_agent_runner)
benchmark_report = runner.run_benchmark()
print(f"Task Success Rate: {benchmark_report['task_success_rate'] * 100}%")
print(f"Average Steps: {benchmark_report['average_steps_to_convergence']}")

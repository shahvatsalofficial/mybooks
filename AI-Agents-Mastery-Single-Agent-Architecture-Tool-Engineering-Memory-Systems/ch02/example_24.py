class HybridEngine:
    def __init__(self, planner: PlanAndSolveOrchestrator, react_runner: EnterpriseAgentRunner):
        self.planner = planner
        self.react = react_runner

    def solve(self, complex_goal: str) -> List[str]:
        self.planner.initialize_plan(complex_goal)
        results = []
        for task in self.planner.plan:
            step_outcome = self.react.run(user_goal=task.description, max_turns=4)
            task.result = step_outcome
            results.append(step_outcome)
        return results

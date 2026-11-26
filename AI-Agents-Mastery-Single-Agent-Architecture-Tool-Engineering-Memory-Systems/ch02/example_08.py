class ReflexionAgent:
    def __init__(self, max_trials: int = 3):
        self.max_trials = max_trials
        self.reflections: List[str] = []

    def run_trial(self, task: str, trial_fn: Callable[[str, List[str]], bool], reflect_fn: Callable[[str, int], str]) -> bool:
        for trial_num in range(1, self.max_trials + 1):
            print(f"
--- TRIAL {trial_num} of {self.max_trials} ---")
            success = trial_fn(task, self.reflections)
            if success:
                print(f"✅ Task converged successfully on trial {trial_num}!")
                return True
                
            # Failure occurred: generate reflection
            reflection = reflect_fn(task, trial_num)
            self.reflections.append(reflection)
            print(f"Generated Reflection: '{reflection}'")
            
        return False

# Verification
def mock_trial(task: str, past_reflections: List[str]) -> bool:
    # Succeeds only if agent has learned to avoid raw SQL
    if any("use parameterization" in r for r in past_reflections):
        return True
    return False

def mock_reflect(task: str, trial: int) -> str:
    return "Next time, use parameterization instead of string interpolation to avoid syntax errors."

reflexion = ReflexionAgent(max_trials=3)
converged = reflexion.run_trial("Execute safe customer query", mock_trial, mock_reflect)
print("Reflexion Final Convergence Status:", converged)

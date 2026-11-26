class AgentTaskStep:
    def __init__(self, step_number: int, action: str, observation: Optional[str] = None):
        self.step_number = step_number
        self.action = action
        self.observation = observation
        self.is_terminal = False

class SteppableAgentRunner:
    def __init__(self, worker_actions: List[str]):
        self.actions = worker_actions
        self.current_step = 0
        self.history: List[AgentTaskStep] = []

    def has_next_step(self) -> bool:
        return self.current_step < len(self.actions)

    def run_step(self) -> AgentTaskStep:
        if not self.has_next_step():
            raise StopIteration("All planned steps completed.")
        
        action_text = self.actions[self.current_step]
        self.current_step += 1
        
        # Execute simulated action
        obs = f"Observation for {action_text}: Verified status OK."
        step = AgentTaskStep(step_number=self.current_step, action=action_text, observation=obs)
        if self.current_step == len(self.actions):
            step.is_terminal = True
            
        self.history.append(step)
        return step

# Verification
stepper = SteppableAgentRunner([
    "query_index('Check user authorization')",
    "query_index('Fetch current account tier')",
    "synthesize_final_answer()"
])

print("Executing Stepper Iteratively:")
while stepper.has_next_step():
    step = stepper.run_step()
    print(f"  Step {step.step_number}: {step.action} -> {step.observation} (Terminal: {step.is_terminal})")

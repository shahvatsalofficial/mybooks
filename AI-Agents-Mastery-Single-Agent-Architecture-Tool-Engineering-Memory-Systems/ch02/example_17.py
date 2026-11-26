from typing import List, Dict

class ReflexionAgent:
    def __init__(self):
        self.reflections: List[str] = []

    def reflect_on_failure(self, task: str, failed_trace: str) -> str:
        reflection = f"In previous attempt for '{task}', I failed because: {failed_trace}. Next time, I must check prerequisite permissions before invoking mutate_state."
        self.reflections.append(reflection)
        print(f"[REFLEXION] Stored verbal reflection ({len(self.reflections)} total)")
        return reflection

    def formulate_next_prompt(self, base_task: str) -> str:
        if not self.reflections:
            return base_task
        guidance = "\n".join([f"- {r}" for r in self.reflections[-3:]])
        return f"{base_task}\n\nPREVIOUS FAILURE LESSONS:\n{guidance}"

ref_agent = ReflexionAgent()
ref_agent.reflect_on_failure("Deploy Microservice", "HTTP 403 Forbidden: Insufficient IAM permissions on ECR registry")
prompt_v2 = ref_agent.formulate_next_prompt("Deploy Microservice")
print("Enhanced Re-attempt Prompt:\n", prompt_v2)

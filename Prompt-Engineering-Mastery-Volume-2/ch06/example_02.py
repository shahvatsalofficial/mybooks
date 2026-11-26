import json
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field
from anthropic import Anthropic

class TestCase(BaseModel):
    input_text: str
    expected_output: str
    category: str

class OptimizationIterationResult(BaseModel):
    iteration: int
    prompt_text: str
    accuracy: float
    failed_cases_count: int

class RecursiveMetaPromptOptimizer:
    def __init__(self, api_key: str, meta_model: str = "claude-3-5-sonnet-20241022"):
        self.client = Anthropic(api_key=api_key)
        self.meta_model = meta_model
        self.target_model = "claude-3-5-haiku-20241022"  # Fast execution tier
        self.history: List[OptimizationIterationResult] = []

    def evaluate_prompt(self, candidate_prompt: str, dataset: List[TestCase]) -> Tuple[float, List[Dict[str, Any]]]:
        passed = 0
        failures = []

        for case in dataset:
            res = self.client.messages.create(
                model=self.target_model,
                max_tokens=300,
                temperature=0.0,
                system=candidate_prompt,
                messages=[{"role": "user", "content": case.input_text}]
            )
            actual_output = res.content[0].text.strip()
            
            # Semantic verification or string containment
            if case.expected_output.lower() in actual_output.lower():
                passed += 1
            else:
                failures.append({
                    "input": case.input_text,
                    "expected": case.expected_output,
                    "actual": actual_output,
                    "category": case.category
                })

        accuracy = passed / len(dataset)
        return accuracy, failures

    def mutate_prompt(self, current_prompt: str, failures: List[Dict[str, Any]], rubric: str) -> str:
        meta_system_instruction = (
            "You are an Elite Prompt Optimization Architect. "
            "Your objective is to examine a current system prompt and a set of failure traces, "
            "then synthesize an improved, higher-performing system prompt.\n\n"
            f"Optimization Rubric:\n{rubric}\n\n"
            "Guidelines:\n"
            "- Eliminate ambiguous phrasing and conversational filler.\n"
            "- Add rigid constraints and boundary assertions addressing the observed failure modes.\n"
            "- Output ONLY the improved system prompt inside <optimized_prompt>...</optimized_prompt> tags."
        )

        user_content = (
            f"CURRENT SYSTEM PROMPT:\n{current_prompt}\n\n"
            f"OBSERVED FAILURES ({len(failures)} cases):\n{json.dumps(failures[:5], indent=2)}\n\n"
            "Diagnose why the current prompt failed on these inputs and generate the optimized prompt."
        )

        res = self.client.messages.create(
            model=self.meta_model,
            max_tokens=1500,
            temperature=0.4,
            system=meta_system_instruction,
            messages=[{"role": "user", "content": user_content}]
        )

        output_text = res.content[0].text
        import re
        match = re.search(r"<optimized_prompt>(.*?)</optimized_prompt>", output_text, re.DOTALL)
        return match.group(1).strip() if match else output_text.strip()

    def run_optimization_loop(
        self,
        initial_prompt: str,
        dataset: List[TestCase],
        rubric: str,
        max_iterations: int = 3
    ) -> str:
        current_prompt = initial_prompt
        best_prompt = initial_prompt
        best_accuracy = -1.0

        for i in range(max_iterations):
            acc, failures = self.evaluate_prompt(current_prompt, dataset)
            print(f"Iteration {i+1}: Accuracy = {acc * 100:.2f}% (Failures: {len(failures)})")
            
            self.history.append(OptimizationIterationResult(
                iteration=i+1,
                prompt_text=current_prompt,
                accuracy=acc,
                failed_cases_count=len(failures)
            ))

            if acc > best_accuracy:
                best_accuracy = acc
                best_prompt = current_prompt

            if acc == 1.0 or not failures:
                print("🏆 100% Benchmark Accuracy Achieved. Optimization converged.")
                break

            current_prompt = self.mutate_prompt(current_prompt, failures, rubric)

        return best_prompt

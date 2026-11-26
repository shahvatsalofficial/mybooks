from typing import List, Dict, Any, Callable

class ProgrammaticAssertionError(Exception):
    pass

class TeleprompterBootstrapper:
    def __init__(
        self,
        client: Anthropic,
        metric_fn: Callable[[str, str], bool],
        max_bootstrapped_demos: int = 3
    ):
        self.client = client
        self.metric_fn = metric_fn
        self.max_demos = max_bootstrapped_demos

    def compile(
        self,
        task_instruction: str,
        unlabeled_training_inputs: List[Dict[str, str]],
        ground_truth_outputs: List[str]
    ) -> List[Dict[str, str]]:
        """
        Runs candidate inputs through zero-shot reasoning, audits outputs with metric_fn,
        and bootstraps passing traces into verified few-shot exemplars.
        """
        bootstrapped_exemplars = []

        for train_in, target_gold in zip(unlabeled_training_inputs, ground_truth_outputs):
            if len(bootstrapped_exemplars) >= self.max_demos:
                break

            prompt = (
                f"Task: {task_instruction}\n\n"
                f"Input: {train_in['text']}\n\n"
                "Think step by step in <scratchpad>...</scratchpad> and emit the final output in <output>...</output>."
            )

            res = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                temperature=0.7,
                system="You are an expert reasoning engine.",
                messages=[{"role": "user", "content": prompt}]
            )
            raw_text = res.content[0].text

            import re
            output_match = re.search(r"<output>(.*?)</output>", raw_text, re.DOTALL)
            predicted_answer = output_match.group(1).strip() if output_match else raw_text.strip()

            # Execute programmatic validation metric
            if self.metric_fn(predicted_answer, target_gold):
                print(f"✅ Bootstrapped valid demonstration for input: {train_in['text'][:40]}...")
                bootstrapped_exemplars.append({
                    "input": train_in["text"],
                    "reasoning_trace": raw_text
                })

        return bootstrapped_exemplars

# Example Metric Validator
def exact_financial_match(predicted: str, gold: str) -> bool:
    # Requires exact normalized entity match
    return predicted.strip().replace("$", "") == gold.strip().replace("$", "")

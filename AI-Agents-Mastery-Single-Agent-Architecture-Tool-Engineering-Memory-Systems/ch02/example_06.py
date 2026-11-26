from collections import Counter

class SelfConsistencyReasoner:
    def __init__(self, samples: int = 5):
        self.samples = samples

    def resolve_consensus(self, prompt: str, llm_sampler_fn: Callable[[str], str]) -> Tuple[str, float]:
        answers = []
        for _ in range(self.samples):
            trajectory = llm_sampler_fn(prompt)
            # Extract final answer
            match = re.search(r"Final Answer:s*(.*)", trajectory, re.IGNORECASE)
            ans = match.group(1).strip() if match else trajectory.strip()
            answers.append(ans)

        # Count frequencies
        counter = Counter(answers)
        most_common_answer, count = counter.most_common(1)[0]
        confidence = round(count / self.samples, 2)
        return most_common_answer, confidence

# Verification
def mock_sampler(prompt: str) -> str:
    # 4 out of 5 return $45.00
    import random
    return "Thought: Checked ledgers. Final Answer: $45.00" if random.random() > 0.2 else "Thought: Final Answer: $50.00"

reasoner = SelfConsistencyReasoner(samples=5)
ans, conf = reasoner.resolve_consensus("What is the calculated discount?", mock_sampler)
print(f"Consensus Answer: '{ans}' with confidence {conf * 100}%")

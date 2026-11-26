import asyncio
import re
from collections import Counter
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field
from openai import AsyncOpenAI

class ConsensusResult(BaseModel):
    winner: str = Field(..., description="Elected consensus answer")
    voting_share: float = Field(..., description="Proportion of paths agreeing with winner")
    total_samples: int = Field(..., description="Total paths evaluated")
    confidence_tier: str = Field(..., description="HIGH (>=80%), MODERATE (>=60%), AMBIGUOUS (<60%)")
    raw_distribution: Dict[str, int] = Field(..., description="Vote count per candidate")
    all_traces: List[str] = Field(..., description="Full reasoning traces for audit logging")

class AsyncSelfConsistencyEngine:
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def _sample_single_path(self, prompt: str, system_prompt: str, temperature: float) -> Tuple[str, str]:
        """Samples a single stochastic reasoning path and extracts the terminal answer."""
        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500
        )
        content = response.choices[0].message.content
        
        # Extract <answer>...</answer> tag
        answer_match = re.search(r"<answer>(.*?)</answer>", content, re.DOTALL)
        if answer_match:
            extracted_answer = answer_match.group(1).strip()
        else:
            # Fallback to last line if tag omitted
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            extracted_answer = lines[-1] if lines else "UNKNOWN"

        return extracted_answer, content

    async def run_consensus(
        self,
        prompt: str,
        system_prompt: str,
        n_samples: int = 7,
        temperature: float = 0.7
    ) -> ConsensusResult:
        tasks = [
            self._sample_single_path(prompt, system_prompt, temperature)
            for _ in range(n_samples)
        ]
        
        # Parallel execution across edge endpoints
        results = await asyncio.gather(*tasks)
        
        answers = [res[0] for res in results]
        traces = [res[1] for res in results]
        
        counter = Counter(answers)
        winner, win_count = counter.most_common(1)[0]
        voting_share = win_count / n_samples
        
        if voting_share >= 0.80:
            tier = "HIGH"
        elif voting_share >= 0.60:
            tier = "MODERATE"
        else:
            tier = "AMBIGUOUS"

        return ConsensusResult(
            winner=winner,
            voting_share=round(voting_share, 4),
            total_samples=n_samples,
            confidence_tier=tier,
            raw_distribution=dict(counter),
            all_traces=traces
        )

# Example Execution Wrapper
async def main():
    engine = AsyncSelfConsistencyEngine(api_key="sk-test-dummy")
    sys_instruction = (
        "Solve the engineering load distribution problem. "
        "Show your work in <reasoning> tags, then output the final numeric recommendation in <answer> tags."
    )
    user_query = "Determine the minimum network MTU size required to avoid IP fragmentation across an IPSec GRE tunnel with a 1500-byte payload."
    # result = await engine.run_consensus(user_query, sys_instruction, n_samples=5)
    # print(result.model_dump_json(indent=2))

if __name__ == "__main__":
    asyncio.run(main())

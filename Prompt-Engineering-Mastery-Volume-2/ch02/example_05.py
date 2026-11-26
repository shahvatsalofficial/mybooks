import asyncio
from typing import List, Dict, Any, Tuple
from collections import Counter
import httpx
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

class MultiProviderConsensusOrchestrator:
    def __init__(self, anthropic_key: str, openai_key: str):
        self.anthropic = AsyncAnthropic(api_key=anthropic_key)
        self.openai = AsyncOpenAI(api_key=openai_key)

    async def _query_claude(self, prompt: str, system_prompt: str, temp: float) -> str:
        res = await self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            temperature=temp,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        return self._extract_answer(res.content[0].text)

    async def _query_openai(self, prompt: str, system_prompt: str, temp: float) -> str:
        res = await self.openai.chat.completions.create(
            model="gpt-4o",
            max_tokens=1000,
            temperature=temp,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return self._extract_answer(res.choices[0].message.content)

    def _extract_answer(self, text: str) -> str:
        import re
        match = re.search(r"<answer>(.*?)</answer>", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        return lines[-1] if lines else "UNKNOWN"

    async def run_heterogeneous_consensus(
        self,
        prompt: str,
        system_prompt: str,
        n_claude: int = 3,
        n_openai: int = 3,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        tasks = []
        for _ in range(n_claude):
            tasks.append(self._query_claude(prompt, system_prompt, temperature))
        for _ in range(n_openai):
            tasks.append(self._query_openai(prompt, system_prompt, temperature))

        all_answers = await asyncio.gather(*tasks)
        total = len(all_answers)
        counts = Counter(all_answers)
        winner, win_count = counts.most_common(1)[0]

        return {
            "elected_consensus": winner,
            "agreement_ratio": win_count / total,
            "total_heterogeneous_samples": total,
            "claude_samples": n_claude,
            "openai_samples": n_openai,
            "vote_distribution": dict(counts),
            "multi_vendor_verified": win_count >= (total * 0.75)
        }

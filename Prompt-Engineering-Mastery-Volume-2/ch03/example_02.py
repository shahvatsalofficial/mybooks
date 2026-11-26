from __future__ import annotations
import asyncio
import re
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field
from anthropic import AsyncAnthropic

class ThoughtNode(BaseModel):
    id: str
    parent_id: Optional[str] = None
    depth: int = 0
    thought_content: str
    score: float = 0.0
    verdict: str = "PENDING"
    children_ids: List[str] = Field(default_factory=list)
    is_terminal: bool = False

class ToTSearchConfig(BaseModel):
    branching_factor: int = Field(3, description="Number of candidate thoughts per node")
    max_depth: int = Field(4, description="Maximum tree search depth")
    beam_width: int = Field(2, description="Top-k states retained per BFS layer")
    prune_threshold: float = Field(0.4, description="Minimum score to avoid pruning")

class TreeOfThoughtsController:
    def __init__(self, api_key: str, config: ToTSearchConfig):
        self.client = AsyncAnthropic(api_key=api_key)
        self.config = config
        self.nodes: Dict[str, ThoughtNode] = {}
        self.node_counter = 0

    def _generate_node_id(self) -> str:
        self.node_counter += 1
        return f"node_{self.node_counter:04d}"

    async def generate_thought_candidates(
        self,
        problem_statement: str,
        current_path: List[str],
        k: int
    ) -> List[str]:
        """Prompts LLM to propose k diverse next-step reasoning thoughts."""
        history = "\n".join([f"Step {idx+1}: {step}" for idx, step in enumerate(current_path)])
        user_prompt = (
            f"Problem: {problem_statement}\n\n"
            f"Current Established Progress:\n{history if history else 'None (Starting)'}\n\n"
            f"Propose exactly {k} distinct, mutually exclusive next logical steps. "
            f"Enclose each proposed step in <thought>...</thought> tags."
        )

        response = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            temperature=0.7,
            system="You are a Tree-of-Thoughts Generator. Propose creative, rigorous next architectural steps.",
            messages=[{"role": "user", "content": user_prompt}]
        )

        content = response.content[0].text
        thoughts = re.findall(r"<thought>(.*?)</thought>", content, re.DOTALL)
        return [t.strip() for t in thoughts][:k]

    async def evaluate_node_state(
        self,
        problem_statement: str,
        current_path: List[str],
        candidate_thought: str
    ) -> Tuple[float, str]:
        """Evaluates a proposed thought against constraints, returning score and verdict."""
        history = "\n".join([f"Step {idx+1}: {step}" for idx, step in enumerate(current_path)])
        eval_prompt = (
            f"Problem: {problem_statement}\n"
            f"Prior Steps:\n{history}\n"
            f"Candidate Next Step: {candidate_thought}\n\n"
            "Evaluate if this candidate step is mathematically and logically sound toward solving the problem.\n"
            "Classify into exactly one verdict: <verdict>SURE</verdict>, <verdict>LIKELY</verdict>, or <verdict>IMPOSSIBLE</verdict>."
        )

        response = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            temperature=0.0,
            system="You are a strict, skeptical heuristic state evaluator.",
            messages=[{"role": "user", "content": eval_prompt}]
        )

        content = response.content[0].text
        if "<verdict>SURE</verdict>" in content:
            return 1.0, "SURE"
        elif "<verdict>LIKELY</verdict>" in content:
            return 0.6, "LIKELY"
        else:
            return 0.0, "IMPOSSIBLE"

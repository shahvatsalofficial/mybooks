from dataclasses import dataclass, field
from typing import Optional
from langchain_openai import ChatOpenAI

@dataclass
class ThoughtNode:
    """A single node in the Tree-of-Thoughts reasoning graph."""
    thought: str
    score: float = 0.0
    depth: int = 0
    parent: Optional["ThoughtNode"] = None
    children: list["ThoughtNode"] = field(default_factory=list)
    is_terminal: bool = False

class TreeOfThoughtsPlanner:
    """
    Production Tree-of-Thoughts planner using BFS with value-guided pruning.
    Generates k candidate thoughts per node and prunes branches scoring below threshold.
    """
    def __init__(self, llm: ChatOpenAI, k: int = 3, max_depth: int = 5, prune_threshold: float = 0.4):
        self.llm = llm
        self.k = k  # Branching factor
        self.max_depth = max_depth
        self.prune_threshold = prune_threshold

    def plan(self, goal: str) -> str:
        """Execute BFS Tree-of-Thoughts search and return the best terminal reasoning path."""
        root = ThoughtNode(thought=f"Goal: {goal}", score=1.0)
        frontier = [root]

        while frontier:
            node = frontier.pop(0)  # BFS: expand shallowest node first

            if node.depth >= self.max_depth:
                if node.score > 0.6:
                    return self._extract_path(node)
                continue

            # Generate k candidate next thoughts
            candidates = self._propose_thoughts(node.thought, goal)

            # Score each candidate
            for thought_text in candidates:
                score = self._evaluate_thought(thought_text, goal)
                child = ThoughtNode(
                    thought=thought_text,
                    score=score,
                    depth=node.depth + 1,
                    parent=node
                )
                node.children.append(child)

                # Only expand nodes above pruning threshold
                if score >= self.prune_threshold:
                    frontier.append(child)

        # Return best leaf if no clean terminal found
        all_leaves = self._get_leaves(root)
        best = max(all_leaves, key=lambda n: n.score)
        return self._extract_path(best)

    def _propose_thoughts(self, current_thought: str, goal: str) -> list[str]:
        prompt = f"""You are a strategic reasoning engine.
Goal: {goal}
Current reasoning state: {current_thought}

Generate exactly {self.k} distinct next reasoning steps, one per line.
Each step must advance toward the goal. Be specific and concrete."""
        response = self.llm.invoke(prompt)
        return [line.strip() for line in response.content.strip().split("\n") if line.strip()][:self.k]

    def _evaluate_thought(self, thought: str, goal: str) -> float:
        prompt = f"""Rate the following reasoning step for achieving the goal.
Goal: {goal}
Reasoning step: {thought}
Return ONLY a decimal score from 0.0 (useless/wrong) to 1.0 (excellent/correct). No other text."""
        response = self.llm.invoke(prompt)
        try:
            return float(response.content.strip())
        except ValueError:
            return 0.5

    def _extract_path(self, node: ThoughtNode) -> str:
        path = []
        current = node
        while current is not None:
            path.append(current.thought)
            current = current.parent
        return "\n".join(reversed(path))

    def _get_leaves(self, node: ThoughtNode) -> list[ThoughtNode]:
        if not node.children:
            return [node]
        leaves = []
        for child in node.children:
            leaves.extend(self._get_leaves(child))
        return leaves

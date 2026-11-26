from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ThoughtNode:
    thought_id: str
    parent_id: Optional[str]
    content: str
    evaluation_score: float = 0.0
    children: List['ThoughtNode'] = field(default_factory=list)

class TreeOfThoughtsSearch:
    def __init__(self, branching_factor: int = 3, max_depth: int = 3):
        self.branching_factor = branching_factor
        self.max_depth = max_depth
        self.root: Optional[ThoughtNode] = None

    def search(self, goal: str, generator_fn: Callable[[str, int], List[str]], evaluator_fn: Callable[[str], float]) -> Optional[ThoughtNode]:
        self.root = ThoughtNode(thought_id="root", parent_id=None, content=goal, evaluation_score=1.0)
        frontier = [self.root]

        for depth in range(self.max_depth):
            next_frontier = []
            for node in frontier:
                # Generate candidate sub-thoughts
                candidates = generator_fn(node.content, self.branching_factor)
                for i, cand in enumerate(candidates):
                    score = evaluator_fn(cand)
                    child = ThoughtNode(
                        thought_id=f"{node.thought_id}_{depth}_{i}",
                        parent_id=node.thought_id,
                        content=cand,
                        evaluation_score=score
                    )
                    node.children.append(child)
                    # Prune branches with scores below threshold
                    if score >= 0.70:
                        next_frontier.append(child)

            if not next_frontier:
                break
            # Sort frontier descending by score to focus search
            frontier = sorted(next_frontier, key=lambda x: x.evaluation_score, reverse=True)[:self.branching_factor]

        # Return best terminating leaf
        return frontier[0] if frontier else None

# Verification
def mock_generator(parent_thought: str, k: int) -> List[str]:
    return [
        f"Hypothesis {i+1}: Approach problem via component decomposition of '{parent_thought[:20]}'"
        for i in range(k)
    ]

def mock_evaluator(thought: str) -> float:
    return 0.85 if "Hypothesis 1" in thought else 0.60

tot = TreeOfThoughtsSearch(branching_factor=2, max_depth=2)
best_leaf = tot.search("Resolve distributed database split-brain anomaly", mock_generator, mock_evaluator)
print("Best Reasoning Path Leaf:", best_leaf.thought_id if best_leaf else "None")

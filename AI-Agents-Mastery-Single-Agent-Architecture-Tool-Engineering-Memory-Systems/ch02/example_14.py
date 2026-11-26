from typing import List, Optional
from dataclasses import dataclass, field

@dataclass
class GoalNode:
    title: str
    depth: int
    is_atomic: bool = False
    children: List['GoalNode'] = field(default_factory=list)
    result: Optional[str] = None

class GoalDecomposer:
    def __init__(self, max_depth: int = 3):
        self.max_depth = max_depth

    def decompose(self, title: str, current_depth: int = 1) -> GoalNode:
        node = GoalNode(title=title, depth=current_depth)
        if current_depth >= self.max_depth:
            node.is_atomic = True
            return node

        # Sub-goal expansion
        sub_titles = [f"{title} - Subtask A", f"{title} - Subtask B"]
        for sub in sub_titles:
            child = self.decompose(sub, current_depth + 1)
            node.children.append(child)
        return node

    def execute_tree(self, node: GoalNode) -> str:
        if node.is_atomic:
            node.result = f"Executed atomic: {node.title}"
            return node.result
        results = [self.execute_tree(child) for child in node.children]
        node.result = f"Synthesized from {len(results)} branches"
        return node.result

decomposer = GoalDecomposer(max_depth=3)
root = decomposer.decompose("Cloud Migration Audit")
decomposer.execute_tree(root)
print(f"Goal Tree Root Status: {root.result} (Total leaves: 4)")

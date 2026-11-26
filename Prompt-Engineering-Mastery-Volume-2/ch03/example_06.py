import math
from typing import List, Optional, Dict, Any

class MCTSNode:
    def __init__(self, state_text: str, parent: Optional[MCTSNode] = None, prior_prob: float = 1.0):
        self.state_text = state_text
        self.parent = parent
        self.prior_prob = prior_prob
        self.children: List[MCTSNode] = []
        self.visit_count: int = 0
        self.total_value: float = 0.0

    @property
    def q_value(self) -> float:
        """Empirical mean value of node."""
        return (self.total_value / self.visit_count) if self.visit_count > 0 else 0.0

    def uct_score(self, c_puct: float = 1.414) -> float:
        """Calculates UCT score for tree descent."""
        if not self.parent:
            return self.q_value
        exploration = c_puct * self.prior_prob * (math.sqrt(self.parent.visit_count) / (1 + self.visit_count))
        return self.q_value + exploration

    def select_best_child(self) -> MCTSNode:
        return max(self.children, key=lambda child: child.uct_score())

    def backpropagate(self, reward: float):
        """Recursively updates visit counts and value up to the root."""
        self.visit_count += 1
        self.total_value += reward
        if self.parent:
            self.parent.backpropagate(reward)

class MCTSReasoningEngine:
    def __init__(self, controller: TreeOfThoughtsController):
        self.controller = controller

    async def run_mcts_simulation(
        self,
        problem: str,
        iterations: int = 20,
        max_depth: int = 4
    ) -> Optional[List[str]]:
        root = MCTSNode(state_text=problem)

        for _ in range(iterations):
            node = root
            path = []

            # 1. Selection
            while node.children and len(path) < max_depth:
                node = node.select_best_child()
                path.append(node.state_text)

            # 2. Expansion
            if len(path) < max_depth and node.visit_count > 0:
                proposals = await self.controller.generate_thought_candidates(
                    problem, path, k=self.controller.config.branching_factor
                )
                for prop in proposals:
                    child = MCTSNode(state_text=prop, parent=node, prior_prob=1.0 / len(proposals))
                    node.children.append(child)
                if node.children:
                    node = node.children[0]
                    path.append(node.state_text)

            # 3. Rollout & Evaluation
            score, verdict = await self.controller.evaluate_node_state(
                problem, path[:-1], path[-1] if path else problem
            )
            reward = 1.0 if verdict == "SURE" else (0.5 if verdict == "LIKELY" else 0.0)

            # 4. Backpropagation
            node.backpropagate(reward)

        # Extract optimal trajectory by highest visit count
        curr = root
        optimal_trajectory = []
        while curr.children:
            curr = max(curr.children, key=lambda c: c.visit_count)
            optimal_trajectory.append(curr.state_text)

        return optimal_trajectory

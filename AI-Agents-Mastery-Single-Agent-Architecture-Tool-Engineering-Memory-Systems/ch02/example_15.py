import math
import random
from typing import List, Dict

class MCTSNode:
    def __init__(self, state_desc: str, parent=None):
        self.state_desc = state_desc
        self.parent = parent
        self.children: List['MCTSNode'] = []
        self.visits = 0
        self.value = 0.0

    def ucb1(self, exploration_constant: float = 1.414) -> float:
        if self.visits == 0:
            return float('inf')
        return (self.value / self.visits) + exploration_constant * math.sqrt(math.log(self.parent.visits) / self.visits)

class AgentMCTSSimulator:
    def __init__(self, iterations: int = 20):
        self.iterations = iterations

    def search_best_action(self, root_desc: str, candidate_actions: List[str]) -> str:
        root = MCTSNode(root_desc)
        for act in candidate_actions:
            root.children.append(MCTSNode(act, parent=root))

        for _ in range(self.iterations):
            # 1. Select
            selected = max(root.children, key=lambda c: c.ucb1())
            # 2. Simulate rollout (mock reward evaluation)
            reward = 1.0 if "safely" in selected.state_desc else 0.4
            reward += random.uniform(-0.1, 0.1)
            # 3. Backpropagate
            selected.visits += 1
            selected.value += reward
            root.visits += 1

        best_child = max(root.children, key=lambda c: c.visits)
        return best_child.state_desc

sim = AgentMCTSSimulator(iterations=50)
best = sim.search_best_action("Root: DB Migration", ["Migrate in-place", "Migrate safely via blue-green shadow"])
print("MCTS Optimal Action Selected:", best)

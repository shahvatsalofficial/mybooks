import math
import random

class MCTSNode:
    def __init__(self, state_desc: str, parent: Optional['MCTSNode'] = None, action_taken: Optional[str] = None):
        self.state_desc = state_desc
        self.parent = parent
        self.action_taken = action_taken
        self.children: List['MCTSNode'] = []
        self.visits = 0
        self.total_reward = 0.0

    def uct_score(self, exploration_weight: float = 1.414) -> float:
        if self.visits == 0:
            return float('inf')
        exploitation = self.total_reward / self.visits
        exploration = exploration_weight * math.sqrt(math.log(self.parent.visits) / self.visits)
        return exploitation + exploration

class MonteCarloAgentPlanner:
    def __init__(self, rollouts: int = 15, max_depth: int = 3):
        self.rollouts = rollouts
        self.max_depth = max_depth

    def plan_next_action(self, root_state: str, action_generator_fn: Callable[[str], List[str]], reward_evaluator_fn: Callable[[str], float]) -> str:
        root = MCTSNode(state_desc=root_state)

        for _ in range(self.rollouts):
            node = root
            depth = 0
            
            # 1. Selection
            while node.children and depth < self.max_depth:
                node = max(node.children, key=lambda c: c.uct_score())
                depth += 1

            # 2. Expansion
            if depth < self.max_depth and node.visits > 0:
                actions = action_generator_fn(node.state_desc)
                for act in actions:
                    child = MCTSNode(state_desc=f"{node.state_desc} -> {act}", parent=node, action_taken=act)
                    node.children.append(child)
                if node.children:
                    node = node.children[0]

            # 3. Simulation & Rollout
            simulated_state = node.state_desc
            reward = reward_evaluator_fn(simulated_state)

            # 4. Backpropagation
            curr = node
            while curr:
                curr.visits += 1
                curr.total_reward += reward
                curr = curr.parent

        # Choose child with highest visit count (most robust)
        best_child = max(root.children, key=lambda c: c.visits)
        return best_child.action_taken or "noop"

# Verification
def mock_action_gen(state: str) -> List[str]:
    return ["check_dependencies", "run_linter", "run_typecheck"]

def mock_reward_eval(state: str) -> float:
    return 0.95 if "run_typecheck" in state else 0.50

mcts = MonteCarloAgentPlanner(rollouts=10)
chosen_action = mcts.plan_next_action("Initial code refactor state", mock_action_gen, mock_reward_eval)
print("MCTS Planned Optimal Action:", chosen_action)

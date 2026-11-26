import heapq
from typing import List, Dict, Optional, Tuple

class PrioritySearchItem:
    def __init__(self, priority: float, path: List[str], depth: int):
        self.priority = priority  # Negative value for max-heap behavior
        self.path = path
        self.depth = depth

    def __lt__(self, other: PrioritySearchItem) -> bool:
        return self.priority < other.priority

class AStarThoughtSearch:
    def __init__(self, controller: TreeOfThoughtsController):
        self.controller = controller

    async def search_astar(
        self,
        problem: str,
        target_goal_depth: int = 4
    ) -> Optional[List[str]]:
        # Priority queue stores tuples: (-f_score, item)
        open_set: List[Tuple[float, PrioritySearchItem]] = []
        
        # Root entry: g = 0, h = 1.0 -> f = 1.0
        root_item = PrioritySearchItem(priority=-1.0, path=[], depth=0)
        heapq.heappush(open_set, (-1.0, root_item))
        
        visited_signatures = set()

        while open_set:
            neg_f, current_item = heapq.heappop(open_set)
            
            if current_item.depth == target_goal_depth:
                return current_item.path

            # Generate child proposals
            proposals = await self.controller.generate_thought_candidates(
                problem, current_item.path, k=self.controller.config.branching_factor
            )

            for prop in proposals:
                new_path = current_item.path + [prop]
                sig = " -> ".join(new_path)
                if sig in visited_signatures:
                    continue
                visited_signatures.add(sig)

                score, verdict = await self.controller.evaluate_node_state(
                    problem, current_item.path, prop
                )
                
                if verdict == "IMPOSSIBLE":
                    continue

                # g(s): path depth penalty; h(s): heuristic score
                g_score = (current_item.depth + 1) * 0.1
                h_score = score
                f_score = h_score - g_score  # Higher is better
                
                child_item = PrioritySearchItem(
                    priority=-f_score,
                    path=new_path,
                    depth=current_item.depth + 1
                )
                heapq.heappush(open_set, (-f_score, child_item))

        return None

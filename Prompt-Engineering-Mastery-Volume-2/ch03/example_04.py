class DFSTreeSearch:
    def __init__(self, controller: TreeOfThoughtsController):
        self.controller = controller
        self.failed_subtrees: List[str] = []

    async def search_dfs(
        self,
        problem: str,
        current_path: List[str],
        depth: int,
        max_depth: int
    ) -> Optional[List[str]]:
        if depth >= max_depth:
            return current_path

        candidates = await self.controller.generate_thought_candidates(
            problem, current_path, k=self.controller.config.branching_factor
        )

        for thought in candidates:
            # Check against failed history
            if thought in self.failed_subtrees:
                continue

            score, verdict = await self.controller.evaluate_node_state(
                problem, current_path, thought
            )

            if verdict == "IMPOSSIBLE" or score < self.controller.config.prune_threshold:
                # Prune branch & log to failure memory
                self.failed_subtrees.append(thought)
                continue

            # Speculatively descend down the tree
            result = await self.search_dfs(
                problem, current_path + [thought], depth + 1, max_depth
            )
            if result is not None:
                return result

            # If result is None, backtracking occurred
            self.failed_subtrees.append(thought)

        return None

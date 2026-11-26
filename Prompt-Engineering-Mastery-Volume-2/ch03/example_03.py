async def execute_bfs(self, problem_statement: str) -> Optional[List[str]]:
        # Root node initialization
        root_id = self._generate_node_id()
        self.nodes[root_id] = ThoughtNode(
            id=root_id,
            thought_content="Root Problem Definition",
            score=1.0,
            verdict="SURE"
        )
        
        current_frontier = [root_id]

        for depth in range(self.config.max_depth):
            candidate_children = []

            for parent_id in current_frontier:
                parent_node = self.nodes[parent_id]
                
                # Reconstruct path from root to current parent
                path_steps = []
                curr = parent_node
                while curr.parent_id is not None:
                    path_steps.append(curr.thought_content)
                    curr = self.nodes[curr.parent_id]
                path_steps.reverse()

                # Generate k thoughts for this parent
                proposals = await self.generate_thought_candidates(
                    problem_statement,
                    path_steps,
                    k=self.config.branching_factor
                )

                # Concurrently evaluate all proposals
                eval_tasks = [
                    self.evaluate_node_state(problem_statement, path_steps, prop)
                    for prop in proposals
                ]
                eval_results = await asyncio.gather(*eval_tasks)

                for prop_text, (score, verdict) in zip(proposals, eval_results):
                    child_id = self._generate_node_id()
                    child_node = ThoughtNode(
                        id=child_id,
                        parent_id=parent_id,
                        depth=depth + 1,
                        thought_content=prop_text,
                        score=score,
                        verdict=verdict
                    )
                    self.nodes[child_id] = child_node
                    parent_node.children_ids.append(child_id)

                    # Filter unviable nodes
                    if score >= self.config.prune_threshold:
                        candidate_children.append(child_id)

            if not candidate_children:
                print(f"Search terminated early at depth {depth}: All branches pruned.")
                break

            # Beam search: select top beam_width candidates by score
            candidate_children.sort(key=lambda nid: self.nodes[nid].score, reverse=True)
            current_frontier = candidate_children[:self.config.beam_width]

            # Check if any top candidate reached a definitive solution
            for nid in current_frontier:
                if self.nodes[nid].verdict == "SURE" and depth == self.config.max_depth - 1:
                    return self._reconstruct_path(nid)

        # Return best path from final frontier
        if current_frontier:
            return self._reconstruct_path(current_frontier[0])
        return None

    def _reconstruct_path(self, terminal_node_id: str) -> List[str]:
        path = []
        curr = self.nodes[terminal_node_id]
        while curr.parent_id is not None:
            path.append(curr.thought_content)
            curr = self.nodes[curr.parent_id]
        path.reverse()
        return path

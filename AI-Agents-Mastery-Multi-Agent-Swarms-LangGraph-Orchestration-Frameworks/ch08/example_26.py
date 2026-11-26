class TrajectoryPruner:
    @staticmethod
    def prune_for_storage(full_trajectory: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Keep only initial user prompt, successful tool calls, and final conclusion
        pruned = [t for t in full_trajectory if t.get("role") in ("user", "assistant_final") or (t.get("role") == "tool" and t.get("exit_code") == 0)]
        print(f"[PRUNING] Compressed trajectory from {len(full_trajectory)} to {len(pruned)} essential items.")
        return pruned

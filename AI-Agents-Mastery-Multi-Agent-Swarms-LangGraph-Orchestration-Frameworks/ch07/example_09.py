class StateCompactor:
    @staticmethod
    def compact_history(historical_checkpoints: List[Dict[str, Any]], retain_count: int = 5) -> List[Dict[str, Any]]:
        if len(historical_checkpoints) <= retain_count:
            return historical_checkpoints
        print(f"[COMPACTION] Pruning {len(historical_checkpoints) - retain_count} old checkpoints...")
        return historical_checkpoints[-retain_count:]

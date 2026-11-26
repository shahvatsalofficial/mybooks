class CheckpointGarbageCollector:
    @staticmethod
    def prune_stale_snapshots(checkpoints: List[Dict[str, Any]], retention_days: int = 7) -> List[Dict[str, Any]]:
        cutoff = time.time() - (retention_days * 86400)
        active = [cp for cp in checkpoints if cp.get("timestamp", 0) >= cutoff or cp.get("is_genesis", False)]
        pruned_count = len(checkpoints) - len(active)
        print(f"[MVCC GC] Purged {pruned_count} historical snapshots older than {retention_days} days.")
        return active

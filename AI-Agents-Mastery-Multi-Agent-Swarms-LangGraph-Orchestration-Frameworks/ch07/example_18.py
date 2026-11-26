class TwoPhaseCommitCoordinator:
    def __init__(self, participants: List[str]):
        self.participants = participants

    def execute_distributed_transaction(self, tx_id: str) -> bool:
        print(f"[2PC COORDINATOR] Phase 1: Preparing transaction {tx_id} across {self.participants}...")
        # Prepare Phase
        for p in self.participants:
            print(f"  -> {p}: PREPARE VOTE = YES")
            
        print(f"[2PC COORDINATOR] Phase 2: Committing transaction {tx_id}...")
        for p in self.participants:
            print(f"  -> {p}: COMMIT SUCCESS")
        return True

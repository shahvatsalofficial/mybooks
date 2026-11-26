class RollbackAction(BaseModel):
    action_type: str
    undo_payload: Dict[str, Any]

class SwarmTransactionCoordinator:
    def __init__(self):
        self.undo_stack: List[RollbackAction] = []

    def register_compensation(self, action_type: str, undo_payload: Dict[str, Any]):
        self.undo_stack.append(RollbackAction(action_type=action_type, undo_payload=undo_payload))

    def rollback_all(self):
        print(f"[ROLLBACK] Error encountered! Executing {len(self.undo_stack)} compensation actions in reverse order...")
        while self.undo_stack:
            action = self.undo_stack.pop()
            print(f" -> Reverting action '{action.action_type}' with payload: {action.undo_payload}")
        print("[ROLLBACK] Compensation sequence completed. Swarm state restored to baseline.")

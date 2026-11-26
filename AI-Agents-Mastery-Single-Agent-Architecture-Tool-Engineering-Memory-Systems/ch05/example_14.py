from typing import List, Callable, Dict, Any

class AgentSagaTransaction:
    def __init__(self):
        self.forward_actions: List[Dict[str, Any]] = []
        self.executed_compensations: List[Callable[[], None]] = []

    def register_step(self, name: str, action: Callable[[], bool], compensate: Callable[[], None]) -> None:
        self.forward_actions.append({"name": name, "action": action, "compensate": compensate})

    def execute_saga(self) -> bool:
        for step in self.forward_actions:
            print(f"[SAGA] Executing step: '{step['name']}'...")
            success = step["action"]()
            if success:
                # Push compensation action onto LIFO rollback stack
                self.executed_compensations.append(step["compensate"])
            else:
                print(f"[SAGA FAILURE] Step '{step['name']}' failed! Initiating rollback...")
                self._rollback()
                return False
        return True

    def _rollback(self) -> None:
        while self.executed_compensations:
            comp_fn = self.executed_compensations.pop()
            comp_fn()
        print("[SAGA ROLLBACK] All compensatory rollback actions completed cleanly.")

saga = AgentSagaTransaction()
saga.register_step("Reserve Inventory", lambda: True, lambda: print("  -> ROLLBACK: Restored inventory count"))
saga.register_step("Charge Credit Card", lambda: True, lambda: print("  -> ROLLBACK: Refunded $450 to card"))
saga.register_step("Generate Shipping Label", lambda: False, lambda: print("  -> ROLLBACK: Voided label"))
saga.execute_saga()

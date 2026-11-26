"""
Compensation Rollback Orchestrator: Executes reverse compensation chains
when an agent workflow encounters an unrecoverable failure in late-stage execution.
"""

from typing import List, Dict, Any, Callable


class CompensationRollbackOrchestrator:
    """Manages transactional undo workflows across distributed agent states."""

    def __init__(self, compensation_registry: Dict[str, Callable[[Dict[str, Any]], bool]]):
        self.compensations = compensation_registry

    def execute_compensation_chain(
        self,
        completed_transitions: List[Dict[str, Any]],
        context_vars: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Walks completed states in reverse order, executing compensating actions.
        Returns execution log of rollback actions.
        """
        rollback_log = []

        for transition in reversed(completed_transitions):
            state_to_undo = transition.get("to")
            if not state_to_undo:
                continue

            handler = self.compensations.get(state_to_undo)
            if handler:
                try:
                    success = handler(context_vars)
                    rollback_log.append({
                        "state_undone": state_to_undo,
                        "status": "SUCCESS" if success else "FAILED"
                    })
                except Exception as exc:
                    rollback_log.append({
                        "state_undone": state_to_undo,
                        "status": "EXCEPTION",
                        "error": str(exc)
                    })
            else:
                rollback_log.append({
                    "state_undone": state_to_undo,
                    "status": "NO_COMPENSATION_REQUIRED"
                })

        return rollback_log

# remediation_multiagent_supervisor.py
# Production architectural fix: Enforces hard delegation ceilings and deadlock breakers.

class MonotonicHandoffGovernor:
    """Enforces acyclic delegation graphs across multi-agent pipelines."""

    MAX_HOPS = 3

    def __init__(self):
        self.active_trajectories: Dict[str, List[str]] = {}

    def process_hop(
        self,
        trace_id: str,
        current_agent: str,
        next_agent: str
    ) -> Tuple[bool, Optional[str]]:
        """Validates that the handoff does not form a circular dependency or exceed depth."""
        path = self.active_trajectories.get(trace_id, [])

        if len(path) >= self.MAX_HOPS:
            return False, (
                f"DEADLOCK_GUARD: Maximum delegation hops ({self.MAX_HOPS}) exceeded. "
                f"Path: {' -> '.join(path)}. Forced fallback to default risk posture."
            )

        if next_agent in path:
            return False, (
                f"CIRCULAR_DEPENDENCY_DETECTED: Agent '{next_agent}' has already participated "
                f"in trace '{trace_id}'. Circular handoffs are strictly forbidden. "
                f"Halting execution and executing abort protocol."
            )

        path.append(current_agent)
        self.active_trajectories[trace_id] = path
        return True, None

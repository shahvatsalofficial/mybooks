class SwarmFailureAuditor:
    @staticmethod
    def audit_for_type_ii_deadlock(agent_turns: List[str]) -> bool:
        """Detects infinite delegation ping-pong between agents."""
        if len(agent_turns) < 4:
            return False
        # Check for A-B-A-B repeating sequence
        if agent_turns[-4:] == [agent_turns[-4], agent_turns[-3], agent_turns[-4], agent_turns[-3]]:
            print("[AUDITOR ALERT] Type II Failure Detected: Infinite Delegation Ping-Pong!")
            return True
        return False

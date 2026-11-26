class SwarmSupervisor:
    def __init__(self, max_turns: int = 6):
        self.name = "CoordinatorSupervisor_01"
        self.role = AgentRole.SUPERVISOR
        self.max_turns = max_turns
        self.history: List[AgentMessage] = []
        self.workers: Dict[AgentRole, AgentProtocol] = {
            AgentRole.RESEARCHER: ResearchWorker(),
            AgentRole.CODER: CodeWorker(),
            AgentRole.AUDITOR: SecurityAuditorWorker()
        }

    def dispatch(self, role: AgentRole, instruction: str) -> AgentMessage:
        worker = self.workers[role]
        msg = AgentMessage(
            sender=self.name,
            sender_role=self.role,
            recipient=worker.name,
            message_type=MessageType.TASK_ASSIGNMENT,
            content=instruction
        )
        self.history.append(msg)
        response = worker.process_message(msg)
        self.history.append(response)
        return response

    def run_objective(self, user_objective: str) -> Dict[str, Any]:
        print(f"[SUPERVISOR] Received Objective: {user_objective}")
        
        # Turn 1: Research specifications
        print("[SUPERVISOR] -> Delegating to Research Specialist...")
        research_res = self.dispatch(AgentRole.RESEARCHER, user_objective)
        print(f"[RESEARCHER RES]: {research_res.content}")

        # Turn 2: Generate production code based on research
        print("[SUPERVISOR] -> Delegating to Code Synthesis Specialist...")
        code_prompt = f"Implement secure implementation based on findings:\n{research_res.content}"
        code_res = self.dispatch(AgentRole.CODER, code_prompt)
        print(f"[CODER RES]:\n{code_res.content}")

        # Turn 3: Security audit of generated code
        print("[SUPERVISOR] -> Delegating to Security Auditor...")
        audit_res = self.dispatch(AgentRole.AUDITOR, code_res.content)
        print(f"[AUDITOR RES]:\n{audit_res.content}")

        # Final Synthesis
        is_approved = audit_res.metadata.get("audit_passed", False)
        final_status = "SUCCESS" if is_approved else "FAILED_AUDIT"
        
        return {
            "status": final_status,
            "turns_used": len(self.history) // 2,
            "final_code": code_res.content,
            "audit_report": audit_res.content,
            "total_messages": len(self.history)
        }

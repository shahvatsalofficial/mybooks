class ToolRBACEnforcer:
    ROLE_PERMISSIONS = {
        "Principal Distributed Systems Architect": ["read_db", "extract_pdf", "web_search"],
        "Staff Technical Publication Strategist": ["web_search", "draft_markdown"]
    }

    @classmethod
    def can_agent_use_tool(cls, agent_role: str, tool_name: str) -> bool:
        allowed = cls.ROLE_PERMISSIONS.get(agent_role, [])
        if tool_name not in allowed:
            print(f"[SECURITY RBAC] DENIED: Agent '{agent_role}' not authorized to use tool '{tool_name}'!")
            return False
        return True

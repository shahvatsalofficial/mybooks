class SubgraphRBACGateway:
    ALLOWED_ROLES_PER_SUBGRAPH = {
        "billing_subgraph": ["finance_auditor", "billing_admin", "tier2_support"],
        "tech_subgraph": ["devops_engineer", "sre_lead", "system_admin"]
    }

    @classmethod
    def authorize_invocation(cls, user_role: str, target_subgraph: str) -> bool:
        allowed = cls.ALLOWED_ROLES_PER_SUBGRAPH.get(target_subgraph, [])
        if user_role not in allowed:
            print(f"[RBAC GATEWAY] ACCESS DENIED: Role '{user_role}' cannot invoke '{target_subgraph}'.")
            return False
        print(f"[RBAC GATEWAY] ACCESS GRANTED: Role '{user_role}' authorized for '{target_subgraph}'.")
        return True

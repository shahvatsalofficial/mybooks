DOMAIN_PACKS = {
    "billing": ["billing_get_invoice", "billing_issue_credit", "billing_check_refund_status"],
    "auth": ["auth_lookup_user", "auth_revoke_sessions", "auth_check_mfa"],
    "infra": ["infra_get_pod_logs", "infra_check_db_latency", "infra_restart_worker"],
}

def resolve_stage_two_tools(selected_domain: str) -> list[str]:
    if selected_domain not in DOMAIN_PACKS:
        raise ValueError(f"Unknown domain '{selected_domain}'.")
    return DOMAIN_PACKS[selected_domain]

# Production Patch: Static Cache Prefix Pinning + User Turn Timestamping
def build_hardened_tenant_request(tenant_id: str, static_policy_text: str, ticket_history: list) -> dict:
    return {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 2048,
        # INVARIANT: System prompt must be 100% static to guarantee KV-cache reuse
        "system": [
            {
                "type": "text",
                "text": "You are the Enterprise Customer Support Agent. Adhere strictly to the operational boundaries below."
            },
            {
                "type": "text",
                "text": f"<enterprise_policy>\n{static_policy_text}\n</enterprise_policy>",
                "cache_control": {"type": "ephemeral"} # Cache the large static corpus
            }
        ],
        # Timestamps are strictly injected inside dynamic user turns, NOT the system prompt
        "messages": [
            {"role": "user", "content": f"[Timestamp: {time.strftime('%Y-%m-%d %H:%M:%SZ')}] User inquiry..."}
        ] + ticket_history[-6:] # Slid to latest 6 turns to prevent token explosion
    }

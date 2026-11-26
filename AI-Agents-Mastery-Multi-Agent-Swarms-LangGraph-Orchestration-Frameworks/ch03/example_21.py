def safe_command_handoff(target_node: str, payload: Dict[str, Any], fallback_node: str = "parent_triage") -> Command:
    try:
        assert target_node != "", "Target node cannot be empty"
        print(f"[COMMAND HANDOFF] Dispatching execution to '{target_node}'...")
        return Command(goto=target_node, update=payload)
    except Exception as exc:
        print(f"[COMMAND FALLBACK] Handoff failed: {exc}. Diverting to '{fallback_node}'...")
        return Command(goto=fallback_node, update={"error": str(exc), "status": "FALLBACK_RECOVERY"})

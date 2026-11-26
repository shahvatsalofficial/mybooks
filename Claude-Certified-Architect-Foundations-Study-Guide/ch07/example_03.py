@dataclass
class MCPToolResult:
    content: str
    is_error: bool = False

class TriageMCPServer:
    """Sharp <12-tool MCP server with read/write separation and HITL gates."""
    TOOLS = [
        "triage_get_ticket", "triage_search_logs", "triage_read_symbol",
        "triage_run_tests", "triage_draft_reply", "triage_post_comment",
        "triage_open_pr", "triage_escalate_sev1",
    ]

    def call_tool(self, name: str, args: dict[str, Any], hitl_approved: bool = False) -> MCPToolResult:
        if name not in self.TOOLS:
            return MCPToolResult(f"UNKNOWN_TOOL: {name}", is_error=True)
        if name in ("triage_post_comment", "triage_open_pr", "triage_escalate_sev1") and not hitl_approved:
            return MCPToolResult("APPROVAL_REQUIRED: Human sign-off needed for mutation.", is_error=True)
        if name == "triage_search_logs" and args.get("hours", 24) > 24:
            return MCPToolResult("INVALID_RANGE: Max log window is 24h.", is_error=True)
        if name == "triage_run_tests":
            return MCPToolResult(json.dumps({"passed": 12, "failed": 0}), is_error=False)
        return MCPToolResult(json.dumps({"ok": True, "tool": name}), is_error=False)

@dataclass
class TriageState:
    ticket_id: str
    turns_used: int = 0
    cache_hits: int = 0
    retries_handled: int = 0
    hitl_paused: bool = False
    final_status: str = "pending"

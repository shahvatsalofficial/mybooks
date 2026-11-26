import json
import os
import anthropic

MODEL = "claude-sonnet-4-20250514"
MUTATING_TOOLS = {"page_oncall"}

TOOLS = [
    {
        "name": "delegate_log_audit",
        "description": "Run an isolated subagent to inspect recent errors for one service.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service": {"type": "string"},
                "window_minutes": {"type": "integer", "minimum": 5, "maximum": 120},
            },
            "required": ["service", "window_minutes"],
            "additionalProperties": False,
        },
    },
    {
        "name": "page_oncall",
        "description": "MUTATING: Page the on-call engineer for a confirmed incident.",
        "input_schema": {
            "type": "object",
            "properties": {
                "team": {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["team", "reason"],
            "additionalProperties": False,
        },
    },
]


def run_log_subagent(client: anthropic.Anthropic, service: str, window_minutes: int) -> str:
    """Isolated worker: receives ONLY a scoped brief, zero parent history."""
    sub_resp = client.messages.create(
        model=MODEL,
        max_tokens=256,
        system="Summarize the probable root cause in 2 concise sentences.",
        messages=[
            {
                "role": "user",
                "content": (
                    f"Scoped Brief: Inspect service='{service}' over last {window_minutes}m. "
                    "Observed telemetry: 142 HTTP 503 errors on /oauth/token; DB pool 100% full."
                ),
            }
        ],
    )
    return "".join(b.text for b in sub_resp.content if b.type == "text").strip()


def require_human_approval(tool_name: str, tool_input: dict) -> bool:
    """Deterministic HITL gate before any state-mutating tool executes."""
    print(f"\n[HITL GATE] Approval requested for '{tool_name}' with {json.dumps(tool_input)}")
    # In production, pause and await signed webhook/UI approval; simulated here:
    return True


def execute_tool(client: anthropic.Anthropic, name: str, args: dict) -> dict:
    if name in MUTATING_TOOLS and not require_human_approval(name, args):
        return {"is_error": True, "content": "Action rejected by human operator."}
    if name == "delegate_log_audit":
        summary = run_log_subagent(client, args["service"], args["window_minutes"])
        return {"is_error": False, "content": summary}
    if name == "page_oncall":
        return {"is_error": False, "content": f"Paged team={args['team']}."}
    return {"is_error": True, "content": f"Unknown tool: {name}"}


def run_triage_loop(ticket_text: str, max_iterations: int = 5) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    messages = [{"role": "user", "content": ticket_text}]

    for step in range(1, max_iterations + 1):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=512,
            system="Diagnose the ticket with delegate_log_audit, then page_oncall if sev1.",
            tools=TOOLS,
            messages=messages,
        )
        print(f"[Step {step}] stop_reason={resp.stop_reason}")

        if resp.stop_reason == "end_turn":
            return "".join(b.text for b in resp.content if b.type == "text").strip()
        if resp.stop_reason == "max_tokens":
            raise RuntimeError("Aborted: response hit max_tokens before completion.")
        if resp.stop_reason == "refusal":
            raise RuntimeError("Aborted: model refused request.")
        if resp.stop_reason != "tool_use":
            raise RuntimeError(f"Aborted: unexpected stop_reason={resp.stop_reason}")

        messages.append({"role": "assistant", "content": resp.content})
        tool_results = []
        for block in resp.content:
            if block.type == "tool_use":
                outcome = execute_tool(client, block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "is_error": outcome["is_error"],
                    "content": outcome["content"],
                })
        messages.append({"role": "user", "content": tool_results})

    raise RuntimeError("Aborted: exceeded max_iterations without end_turn.")


if __name__ == "__main__":
    result = run_triage_loop("Customers report OAuth token refresh 503s in eu-west-1.")
    print("\nFinal Summary:", result)

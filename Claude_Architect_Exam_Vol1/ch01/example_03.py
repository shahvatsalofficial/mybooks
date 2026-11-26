def run_flexible_diagnostic(incident_text: str) -> dict:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        system=(
            "If the incident has enough detail, call classify_ticket. "
            "If it is empty or ambiguous, ask one concise clarifying question."
        ),
        tools=[TRIAGE_TOOL],
        tool_choice={"type": "auto"},
        messages=[{"role": "user", "content": incident_text}],
    )
    if response.stop_reason == "tool_use":
        tool_block = next(b for b in response.content if b.type == "tool_use")
        ticket = TriageTicket.model_validate(tool_block.input)
        return {"status": "classified", "ticket": ticket.model_dump()}
    if response.stop_reason == "end_turn":
        text = "".join(b.text for b in response.content if b.type == "text")
        return {"status": "needs_info", "message": text.strip()}
    raise RuntimeError(f"Unhandled stop_reason: {response.stop_reason}")

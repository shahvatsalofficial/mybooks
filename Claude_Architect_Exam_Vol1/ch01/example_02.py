def run_diagnostic_with_retry(incident_text: str) -> TriageTicket:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    for budget in (512, 1024):
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=budget,
            system="Classify the support incident using the classify_ticket tool only.",
            tools=[TRIAGE_TOOL],
            tool_choice={"type": "tool", "name": "classify_ticket"},
            messages=[{"role": "user", "content": incident_text}],
        )
        if response.stop_reason == "max_tokens":
            continue
        if response.stop_reason != "tool_use":
            raise RuntimeError(f"Unexpected stop_reason: {response.stop_reason}")
        tool_block = next(b for b in response.content if b.type == "tool_use")
        return TriageTicket.model_validate(tool_block.input)
    raise RuntimeError("Output truncated even at max_tokens=1024.")

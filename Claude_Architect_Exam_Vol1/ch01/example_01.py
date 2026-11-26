import json
import os
from typing import Literal
import anthropic
from pydantic import BaseModel, Field, ValidationError


class TriageTicket(BaseModel):
    severity: Literal["sev1", "sev2", "sev3"]
    component: Literal["auth", "billing", "ingestion", "unknown"]
    summary: str = Field(min_length=10, max_length=160)
    requires_human_approval: bool


TRIAGE_TOOL = {
    "name": "classify_ticket",
    "description": "Emit a validated triage classification for a support incident.",
    "input_schema": {
        "type": "object",
        "properties": {
            "severity": {"type": "string", "enum": ["sev1", "sev2", "sev3"]},
            "component": {"type": "string", "enum": ["auth", "billing", "ingestion", "unknown"]},
            "summary": {"type": "string", "minLength": 10, "maxLength": 160},
            "requires_human_approval": {"type": "boolean"},
        },
        "required": ["severity", "component", "summary", "requires_human_approval"],
        "additionalProperties": False,
    },
}


def run_diagnostic(incident_text: str) -> TriageTicket:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        system="Classify the support incident using the classify_ticket tool only.",
        tools=[TRIAGE_TOOL],
        tool_choice={"type": "tool", "name": "classify_ticket"},
        messages=[{"role": "user", "content": incident_text}],
    )

    print(f"Observed stop_reason: {response.stop_reason}")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("Output truncated at max_tokens; increase budget or split task.")
    if response.stop_reason != "tool_use":
        raise RuntimeError(f"Expected tool_use, got {response.stop_reason}")

    tool_block = next(b for b in response.content if b.type == "tool_use")
    return TriageTicket.model_validate(tool_block.input)


if __name__ == "__main__":
    sample = "EU customers receive HTTP 503 on OAuth token refresh since 02:10 UTC."
    try:
        ticket = run_diagnostic(sample)
        print("Validated JSON:", json.dumps(ticket.model_dump(), indent=2))
    except ValidationError as exc:
        print("Schema validation failed:", exc)

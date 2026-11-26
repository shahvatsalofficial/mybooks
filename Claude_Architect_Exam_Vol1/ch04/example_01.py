import json
from typing import Literal
from pydantic import BaseModel, Field, model_validator

class TriageDecision(BaseModel):
    category: Literal["billing", "outage", "auth", "feature_request"]
    severity: Literal["sev1", "sev2", "sev3"]
    requires_human_review: bool
    auto_credit_usd: float = Field(ge=0.0, le=50.0)
    rationale: str = Field(max_length=240)

    @model_validator(mode="after")
    def enforce_sev1_escalation(self) -> "TriageDecision":
        if self.severity == "sev1" and not self.requires_human_review:
            raise ValueError("sev1 incidents must require human review")
        return self

def build_tool_definition() -> dict:
    return {
        "name": "record_triage_decision",
        "description": "Record the structured triage classification for a support ticket.",
        "input_schema": TriageDecision.model_json_schema(),
    }

def validate_tool_payload(raw_tool_input: dict) -> TriageDecision:
    return TriageDecision.model_validate(raw_tool_input)

if __name__ == "__main__":
    tool_def = build_tool_definition()
    print("Schema keys:", list(tool_def["input_schema"]["properties"].keys()))

    sample_response = {
        "category": "outage",
        "severity": "sev1",
        "requires_human_review": True,
        "auto_credit_usd": 0.0,
        "rationale": "Production webhook endpoints returning HTTP 503 across us-east.",
    }
    decision = validate_tool_payload(sample_response)
    print("Validated:", json.dumps(decision.model_dump()))

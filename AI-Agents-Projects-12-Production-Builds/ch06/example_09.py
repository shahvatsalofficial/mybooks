from __future__ import annotations

from pydantic import BaseModel

SPAM_TRIGGERS = ("act now", "100% free", "guaranteed roi", "urgent response required", "click here immediately")


class ComplianceReport(BaseModel):
    compliant: bool
    violations: list[str]


def validate_outbound_compliance(subject: str, body: str, has_unsubscribe_footer: bool) -> ComplianceReport:
    violations: list[str] = []
    combined = f"{subject} {body}".lower()

    for phrase in SPAM_TRIGGERS:
        if phrase in combined:
            violations.append(f"spam_trigger:{phrase}")

    if body.count("!") > 1:
        violations.append("excessive_exclamation_marks")
    if len(subject) > 78:
        violations.append(f"subject_too_long:{len(subject)}")
    if not has_unsubscribe_footer:
        violations.append("missing_unsubscribe_footer")

    return ComplianceReport(compliant=len(violations) == 0, violations=violations)


if __name__ == "__main__":
    res = validate_outbound_compliance(
        subject="SOC2 & Kubernetes reliability for Acme Cloud",
        body="Hi Priya, noticed your Q3 2026 SOC2 Type II milestone. Would love to share how platform teams automate triage.",
        has_unsubscribe_footer=True,
    )
    print(res.model_dump_json())

from __future__ import annotations

from pydantic import BaseModel


class VerifiedEvidence(BaseModel):
    evidence_id: str
    source: str
    fact_text: str
    allowed_entities: list[str]


class EvidenceRegistry:
    def __init__(self, items: list[VerifiedEvidence]) -> None:
        self._items = items

    def allowed_tokens(self) -> set[str]:
        tokens: set[str] = set()
        for item in self._items:
            for ent in item.allowed_entities:
                tokens.add(ent.lower())
        return tokens

    def format_grounding_context(self) -> str:
        return "\n".join(f"[{it.evidence_id} | {it.source}] {it.fact_text}" for it in self._items)


if __name__ == "__main__":
    reg = EvidenceRegistry([
        VerifiedEvidence(
            evidence_id="EV-01",
            source="clearbit",
            fact_text="Acme Cloud Ltd operates with 640 employees in B2B Cloud Infrastructure.",
            allowed_entities=["Acme Cloud Ltd", "640", "B2B Cloud Infrastructure"],
        ),
        VerifiedEvidence(
            evidence_id="EV-02",
            source="technographics",
            fact_text="Engineering stack includes Kubernetes, Terraform, and Snowflake.",
            allowed_entities=["Kubernetes", "Terraform", "Snowflake"],
        ),
        VerifiedEvidence(
            evidence_id="EV-03",
            source="press_release",
            fact_text="Published SOC2 Type II attestation in Q3 2026.",
            allowed_entities=["SOC2 Type II", "Q3 2026"],
        ),
    ])
    print(reg.format_grounding_context())

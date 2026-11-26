from __future__ import annotations

MEDDIC_DISCOVERY_PROMPTS: dict[str, str] = {
    "identified_pain": "Which part of your current deployment or incident workflow creates the most manual toil for your platform team?",
    "decision_timeline": "Are you targeting a production rollout in the current quarter, or evaluating architectures for next fiscal year?",
    "economic_buyer": "Who typically owns the reliability or platform budget sign-off for tooling in this category?",
}


def detect_meddic_gaps(breakdown: dict[str, int]) -> list[tuple[str, str]]:
    gaps: list[tuple[str, str]] = []
    if breakdown.get("identified_pain", 0) == 0:
        gaps.append(("identified_pain", MEDDIC_DISCOVERY_PROMPTS["identified_pain"]))
    if breakdown.get("decision_timeline", 0) == 0:
        gaps.append(("decision_timeline", MEDDIC_DISCOVERY_PROMPTS["decision_timeline"]))
    if breakdown.get("economic_buyer", 0) < 15:
        gaps.append(("economic_buyer", MEDDIC_DISCOVERY_PROMPTS["economic_buyer"]))
    return gaps


if __name__ == "__main__":
    partial_breakdown = {
        "firmographic_fit": 20,
        "economic_buyer": 8,
        "decision_criteria_tech": 15,
        "behavioral_intent": 14,
        "identified_pain": 0,
        "decision_timeline": 0,
    }
    for pillar, question in detect_meddic_gaps(partial_breakdown):
        print(f"[{pillar}] -> {question}")

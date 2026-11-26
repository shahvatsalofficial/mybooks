from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class RoutingTier(str, Enum):
    TIER_A_AE_FAST_TRACK = "tier_a_ae_fast_track"
    TIER_B_SDR_OUTREACH = "tier_b_sdr_outreach"
    TIER_C_NURTURE = "tier_c_nurture"


class MeddicInputs(BaseModel):
    employee_count: int = Field(ge=1)
    is_economic_buyer_or_vp: bool
    has_target_tech_stack: bool
    decayed_intent_score: float = Field(ge=0.0, le=100.0)
    explicit_pain_identified: bool
    timeline_under_90_days: bool


class MeddicScorecard(BaseModel):
    total_score: int = Field(ge=0, le=100)
    breakdown: dict[str, int]
    routing_tier: RoutingTier


def score_meddic_lead(inp: MeddicInputs) -> MeddicScorecard:
    firm_pts = 20 if inp.employee_count >= 250 else (12 if inp.employee_count >= 50 else 5)
    buyer_pts = 20 if inp.is_economic_buyer_or_vp else 8
    tech_pts = 15 if inp.has_target_tech_stack else 4
    intent_pts = round(min(25.0, inp.decayed_intent_score * 0.25))
    pain_pts = 12 if inp.explicit_pain_identified else 0
    timeline_pts = 8 if inp.timeline_under_90_days else 0

    total = min(100, firm_pts + buyer_pts + tech_pts + intent_pts + pain_pts + timeline_pts)
    if total >= 75:
        tier = RoutingTier.TIER_A_AE_FAST_TRACK
    elif total >= 50:
        tier = RoutingTier.TIER_B_SDR_OUTREACH
    else:
        tier = RoutingTier.TIER_C_NURTURE

    return MeddicScorecard(
        total_score=total,
        breakdown={
            "firmographic_fit": firm_pts,
            "economic_buyer": buyer_pts,
            "decision_criteria_tech": tech_pts,
            "behavioral_intent": intent_pts,
            "identified_pain": pain_pts,
            "decision_timeline": timeline_pts,
        },
        routing_tier=tier,
    )


if __name__ == "__main__":
    lead_inp = MeddicInputs(
        employee_count=640,
        is_economic_buyer_or_vp=True,
        has_target_tech_stack=True,
        decayed_intent_score=57.33,
        explicit_pain_identified=True,
        timeline_under_90_days=True,
    )
    print(score_meddic_lead(lead_inp).model_dump_json(indent=2))

import asyncio
from typing import Dict, Any, List
from pydantic import BaseModel, Field

class ClinicalDosageDecision(BaseModel):
    patient_id: str
    weight_kg: float
    recommended_dose_mg: float
    consensus_confidence: float = Field(..., ge=0.0, le=1.0)
    audit_verdict: str  # APPROVED | HUMAN_INTERVENTION_REQUIRED

class GuardedClinicalRuntime:
    def __init__(self, engine: AsyncSelfConsistencyEngine, threshold: float = 0.90):
        self.engine = engine
        self.safety_threshold = threshold

    async def evaluate_patient_dose(self, patient_chart: Dict[str, Any]) -> ClinicalDosageDecision:
        query = (
            f"Patient ID: {patient_chart['id']}\n"
            f"Weight: {patient_chart['weight_kg']} kg\n"
            f"Renal Function (eGFR): {patient_chart['egfr']} mL/min\n"
            "Calculate recommended daily methotrexate adjuvant dose in milligrams."
        )
        sys_prompt = (
            "You are a clinical pharmacokinetics engine. Conduct step-by-step weight-adjusted dosage calculations "
            "inside <scratchpad>...</scratchpad> and output ONLY the final numeric dose in milligrams inside <answer>...</answer>."
        )

        # 11 stochastic paths evaluated in parallel
        consensus = await self.engine.run_consensus(query, sys_prompt, n_samples=11, temperature=0.7)
        
        # Rigorous safety threshold enforcement
        if consensus.voting_share < self.safety_threshold:
            return ClinicalDosageDecision(
                patient_id=patient_chart["id"],
                weight_kg=patient_chart["weight_kg"],
                recommended_dose_mg=0.0,
                consensus_confidence=consensus.voting_share,
                audit_verdict="HUMAN_INTERVENTION_REQUIRED"
            )

        return ClinicalDosageDecision(
            patient_id=patient_chart["id"],
            weight_kg=patient_chart["weight_kg"],
            recommended_dose_mg=float(consensus.winner),
            consensus_confidence=consensus.voting_share,
            audit_verdict="APPROVED"
        )

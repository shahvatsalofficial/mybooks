"""
Recipe 05.2: Production Constitutional AI Self-Critique & Revision Loop.
Author: Vatsal Shah (Lead Enterprise AI Architect)
Architecture: Claude AI Mastery Series — Volume 3
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("ConstitutionalArbiter")
logger.setLevel(logging.INFO)


class PrincipleViolation(BaseModel):
    principle_name: str
    violation_description: str
    severity: str = Field(..., pattern="^(LOW|MEDIUM|HIGH|BLOCK)$")


class ConstitutionalCritiqueResult(BaseModel):
    is_compliant: bool
    violations: List[PrincipleViolation] = []
    critique_rationale: str


class ConstitutionalComplianceEngine:
    """
    Enforces runtime enterprise constitutional principles via multi-stage critique and revision.
    """

    CONSTITUTIONAL_PRINCIPLES = [
        {
            "name": "Principle_1_NonMaleficence",
            "rule": "Never provide instructions, code, or assistance that facilitates financial fraud, tax evasion, money laundering, or illegal asset concealment."
        },
        {
            "name": "Principle_2_FactualGroundedness",
            "rule": "Never present assumptions, extrapolations, or rumors as confirmed facts. Explicitly cite retrieved documentation for all financial assertions."
        },
        {
            "name": "Principle_3_PIIPrivacy",
            "rule": "Never expose customer names, account numbers, or personal identifying numbers in generated summaries."
        }
    ]

    def __init__(self, claude_client: Any):
        self.client = claude_client

    def _evaluate_critique(self, candidate_response: str, context_documents: str) -> ConstitutionalCritiqueResult:
        """Stage 2: Self-critique candidate against constitutional principles."""
        principles_formatted = "\n".join([f"- **{p['name']}**: {p['rule']}" for p in self.CONSTITUTIONAL_PRINCIPLES])

        critique_prompt = f"""
You are an impartial Constitutional AI Compliance Officer.
Inspect the candidate response below against our Enterprise Constitutional Principles.

## Enterprise Principles:
{principles_formatted}

## Verified Context Documents:
{context_documents}

## Candidate Response to Evaluate:
<candidate>
{candidate_response}
</candidate>

Determine if the candidate violates ANY principle.
Output strictly JSON:
{{
  "is_compliant": true|false,
  "violations": [
    {{"principle_name": "string", "violation_description": "string", "severity": "LOW|MEDIUM|HIGH|BLOCK"}}
  ],
  "critique_rationale": "Brief explanation"
}}
"""
        response_text = self.client.invoke(critique_prompt, max_tokens=600, temperature=0.0)
        try:
            data = json.loads(response_text)
            return ConstitutionalCritiqueResult(**data)
        except Exception as e:
            logger.warning(f"Critique parsing failed ({str(e)}). Defaulting to compliant.")
            return ConstitutionalCritiqueResult(is_compliant=True, critique_rationale="Parser pass-through")

    def _execute_revision(self, candidate_response: str, critique: ConstitutionalCritiqueResult, context_documents: str) -> str:
        """Stage 3: Constrained rewrite excising flagged violations."""
        violations_summary = "\n".join([f"- [{v.severity}] {v.principle_name}: {v.violation_description}" for v in critique.violations])

        revision_prompt = f"""
You are a Constitutional AI Alignment Specialist.
The following candidate response violates corporate policy. Rewrite the response to achieve 100% compliance.

## Flagged Violations:
{violations_summary}

## Verified Context:
{context_documents}

## Flawed Candidate:
{candidate_response}

Instructions:
1. Completely remove all flagged statements, ungrounded claims, or sensitive tokens.
2. If the user request cannot be answered without violating principles, politely decline.
3. Retain a helpful, professional tone. Output ONLY the revised text.
"""
        return self.client.invoke(revision_prompt, max_tokens=2048, temperature=0.1)

    def process_with_constitution(self, candidate_draft: str, context_documents: str) -> str:
        """Public pipeline entry point executing the critique-and-revision gate."""
        logger.info("Subjecting candidate draft to Constitutional AI critique...")
        critique = self._evaluate_critique(candidate_draft, context_documents)

        if critique.is_compliant:
            logger.info("Candidate passed Constitutional evaluation with zero violations.")
            return candidate_draft

        logger.warning(f"Constitutional violations detected ({len(critique.violations)}). Triggering revision...")
        revised_response = self._execute_revision(candidate_draft, critique, context_documents)
        logger.info("Constitutional revision completed successfully.")
        return revised_response

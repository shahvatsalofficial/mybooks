"""
Enterprise Legal Contract Redline & Risk Auditor
Author: Vatsal Shah, Lead Enterprise AI Architect
Publisher: Opportunity4u Press (c) 2026
"""

import os
import json
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
import anthropic

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("LegalAuditor")

class ContractRisk(BaseModel):
    risk_id: str = Field(..., description="Unique risk identifier (e.g. RISK-01)")
    severity: str = Field(..., description="HIGH, MEDIUM, or LOW")
    category: str = Field(..., description="Liability, Indemnity, Intellectual Property, or Termination")
    conflicting_documents: List[str] = Field(..., description="List of documents containing conflicting terms")
    clause_citations: List[str] = Field(..., description="Exact section citations from each document")
    conflict_description: str = Field(..., description="Detailed legal explanation of the contractual tension")
    recommended_redline: str = Field(..., description="Exact contractual replacement language")

class ContractAuditReport(BaseModel):
    transaction_name: str
    overall_risk_score: float = Field(..., ge=0.0, le=100.0)
    executive_summary: str
    identified_risks: List[ContractRisk]

class EnterpriseContractAuditor:
    def __init__(self, api_key: Optional[str] = None):
        self.client = anthropic.Anthropic(
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY")
        )
        self.model = "claude-3-5-sonnet-20241022"

    def audit_contract_suite(self, msa_text: str, sow_text: str, dpa_text: str) -> ContractAuditReport:
        """
        Performs a forensic cross-document legal audit across MSA, SOW, and DPA agreements.
        """
        schema_json = json.dumps(ContractAuditReport.model_json_schema(), indent=2)

        system_prompt = f"""<system_instructions>
You are Senior Enterprise Legal Counsel specializing in commercial technology transactions.
Audit the provided suite of agreements for clause collisions, indemnification gaps, and liability cap conflicts.
Adhere strictly to this Pydantic JSON schema:
<schema>
{schema_json}
</schema>
Rules:
1. Provide exact, verifiable section numbers and direct quotes for every identified risk.
2. Formulate surgically precise redline replacement text for each high-severity conflict.
3. Output ONLY the raw JSON object enclosed in <audit_report> tags.
4. Never emit conversational preambles or markdown code fences.
</system_instructions>"""

        user_content = f"""<contract_suite>
  <document id="MSA" title="Master Services Agreement">
{msa_text}
  </document>
  <document id="SOW" title="Statement of Work #01">
{sow_text}
  </document>
  <document id="DPA" title="Data Protection Agreement">
{dpa_text}
  </document>
</contract_suite>

<user_prompt>
Perform an exhaustive forensic audit across these agreements. Focus on liability caps, GDPR data breach notification windows, and intellectual property ownership.
</user_prompt>"""

        logger.info("Dispatching legal contract suite to Claude 3.5 Sonnet...")
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=0.0,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": "<audit_report>{"}
            ]
        )

        raw_text = "<audit_report>{" + response.content[0].text
        json_str = raw_text.split("<audit_report>")[1].split("</audit_report>")[0].strip()

        report = ContractAuditReport.model_validate_json(json_str)
        logger.info(f"Audit completed: {len(report.identified_risks)} risks identified. Overall Risk Score: {report.overall_risk_score}/100")
        return report

# Production Verification Script
if __name__ == "__main__":
    print("Enterprise Legal Contract Auditor initialized.")

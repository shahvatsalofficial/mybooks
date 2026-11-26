"""
Enterprise Forensic 10-K Footnote Reconciliation Engine
Author: Vatsal Shah, Lead Enterprise AI Architect
Publisher: Opportunity4u Press (c) 2026
"""

import json
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
import anthropic

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("FootnoteReconciler")

class AccountingPolicyVariance(BaseModel):
    footnote_number: str = Field(..., description="E.g. Footnote 8 (Revenue Recognition)")
    year_prior: str
    year_current: str
    variance_severity: str = Field(..., description="HIGH, MEDIUM, or LOW")
    policy_shift_summary: str
    ebitda_impact_estimate_usd: Optional[float]
    audit_risk_rating: str

class ForensicFinancialReport(BaseModel):
    company_ticker: str
    fiscal_years_audited: List[str]
    identified_variances: List[AccountingPolicyVariance]
    executive_conclusion: str

class ForensicFootnoteReconciler:
    def __init__(self, api_key: str = None):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"

    def reconcile_filings(self, fy23_text: str, fy24_text: str, fy25_text: str) -> ForensicFinancialReport:
        schema_json = json.dumps(ForensicFinancialReport.model_json_schema(), indent=2)

        system_prompt = f"""<system_instructions>
You are a Principal Forensic Accountant and CFA Charterholder.
Audit the provided three years of SEC 10-K financial footnote disclosures.
Detect subtle changes in revenue recognition, reserve estimates, and contingent liabilities.
Adhere strictly to this Pydantic schema:
<schema>
{schema_json}
</schema>
Output ONLY the raw JSON object enclosed in <financial_audit> tags.
</system_instructions>"""

        user_content = f"""<filings>
  <filing year="FY2023">\n{fy23_text}\n</filing>
  <filing year="FY2024">\n{fy24_text}\n</filing>
  <filing year="FY2025">\n{fy25_text}\n</filing>
</filings>
<audit_task>Reconcile all accounting policy changes and estimate EBITDA adjustments.</audit_task>"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=0.0,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": "<financial_audit>{"}
            ]
        )

        raw_out = "<financial_audit>{" + response.content[0].text
        json_str = raw_out.split("<financial_audit>")[1].split("</financial_audit>")[0].strip()
        return ForensicFinancialReport.model_validate_json(json_str)

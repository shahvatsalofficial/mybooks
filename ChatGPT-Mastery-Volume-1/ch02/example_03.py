from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from openai import OpenAI

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class SecurityFinding(BaseModel):
    vulnerability_id: str = Field(description="CVE or internal vulnerability code")
    risk_level: RiskLevel
    affected_endpoints: List[str]
    remediation_steps: str

class SecurityAuditReport(BaseModel):
    audit_id: str
    overall_score: float = Field(ge=0.0, le=100.0)
    findings: List[SecurityFinding]
    executive_summary: str

client = OpenAI()

def execute_pydantic_audit(system_logs: str) -> SecurityAuditReport:
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content": "You are an automated penetration test parser."},
            {"role": "user", "content": system_logs}
        ],
        response_format=SecurityAuditReport,
        temperature=0.0,
    )
    # Guaranteed instance of SecurityAuditReport with full runtime type guarantees
    return completion.choices[0].message.parsed

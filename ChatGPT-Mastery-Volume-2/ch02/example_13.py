"""
Hands-On Lab: Self-Healing Financial Extraction Pipeline
Demonstrates Instructor-based automatic schema auto-correction.
"""
from typing import List
from pydantic import BaseModel, Field, field_validator, ConfigDict
import instructor
from openai import OpenAI

# Initialize patched Instructor client
client = instructor.from_openai(OpenAI())

class SegmentFinancialMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")
    segment_name: str = Field(description="Business operational division (e.g., Cloud, Consumer, Advertising)")
    revenue_billions: float = Field(description="Segment revenue in billions of USD")
    operating_margin_pct: float = Field(description="Operating margin percentage, e.g., 28.5")

    @field_validator("revenue_billions")
    @classmethod
    def validate_positive_revenue(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"Revenue cannot be negative. Found: {v}")
        return v

class CorporateQuarterlyReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company_name: str
    fiscal_quarter: str = Field(description="e.g., Q3 2026")
    total_reported_revenue_billions: float
    segments: List[SegmentFinancialMetric]

    @field_validator("segments")
    @classmethod
    def validate_segment_revenue_reconciliation(cls, segments: List[SegmentFinancialMetric], info):
        # Business logic validation: Sum of segments must closely match total reported revenue
        values = info.data
        if "total_reported_revenue_billions" in values:
            total_reported = values["total_reported_revenue_billions"]
            segment_sum = sum(s.revenue_billions for s in segments)
            discrepancy = abs(total_reported - segment_sum)
            # Allow max 5% rounding discrepancy
            if discrepancy > (total_reported * 0.05):
                raise ValueError(
                    f"Financial Reconciliation Error: Total revenue is {total_reported}B, but sum of segments "
                    f"is {segment_sum:.2f}B (Discrepancy of {discrepancy:.2f}B exceeds 5% threshold). "
                    f"Re-audit individual segment revenues."
                )
        return segments

def run_extraction_lab():
    transcript_sample = """
    Acme Global Technologies reported fiscal Q3 2026 results. Total consolidated revenue reached 50.0 billion dollars.
    Our Cloud Computing division led performance with 32.5 billion in revenue at a 38% operating margin.
    Consumer Hardware brought in 12.0 billion at a 15% margin.
    Digital Enterprise software contributed 5.5 billion at a 42% margin.
    """
    
    print("
--- Initiating Self-Healing Extraction ---")
    report = client.chat.completions.create(
        model="gpt-4o",
        response_model=CorporateQuarterlyReport,
        max_retries=3, # Automatically retries if @field_validator fails!
        messages=[
            {"role": "system", "content": "Extract corporate quarterly financial statements with mathematical precision."},
            {"role": "user", "content": transcript_sample}
        ]
    )
    
    print("
✅ Successfully Extracted & Validated Financial Report:")
    print(f"Company: {report.company_name} ({report.fiscal_quarter})")
    print(f"Total Revenue: ${report.total_reported_revenue_billions}B")
    print("Segment Breakdown:")
    for s in report.segments:
        print(f"  • {s.segment_name}: ${s.revenue_billions}B ({s.operating_margin_pct}% margin)")

if __name__ == "__main__":
    run_extraction_lab()

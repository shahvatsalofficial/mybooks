class ArchitecturalAdvisoryOutput(BaseModel):
    executive_summary: str = Field(description="Concise 3-sentence summary")
    primary_recommendation: str = Field(description="The definitive technical recommendation")
    risk_score: int = Field(ge=1, le=10, description="Risk severity on 1-10 scale")
    compliance_passed: bool = Field(description="True if architecture satisfies PCI-DSS")

# Task enforcing structured Pydantic output
structured_task = Task(
    description="Analyze cloud checkpointing architecture and emit formal compliance assessment.",
    expected_output="An ArchitecturalAdvisoryOutput Pydantic object.",
    output_pydantic=ArchitecturalAdvisoryOutput,
    agent=cloud_researcher
)

class SwarmEvaluationScore(BaseModel):
    trajectory_efficiency: int = Field(ge=1, le=5, description="1: Excessive loops, 5: Minimal necessary turns")
    context_isolation: int = Field(ge=1, le=5, description="1: Data leakage, 5: Perfect private state boundaries")
    factual_faithfulness: int = Field(ge=1, le=5, description="1: Pure hallucination, 5: Fully grounded in tool data")
    overall_score: float = Field(ge=0.0, le=100.0)
    verdict: Literal["PASS", "NEEDS_REVISION", "FAIL"]
    critique_summary: str

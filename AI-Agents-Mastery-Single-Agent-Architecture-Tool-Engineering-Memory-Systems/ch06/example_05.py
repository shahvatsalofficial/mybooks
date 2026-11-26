class ExtractedFilters(BaseModel):
    fiscal_year: Optional[int] = Field(description="Target fiscal year (e.g. 2024, 2025)")
    department: Optional[str] = Field(description="Target department: engineering, finance, legal, hr")
    confidentiality: str = Field(default="public", description="public, internal, restricted")

class MetadataFilterExtractor:
    @staticmethod
    def extract_filters(prompt: str) -> ExtractedFilters:
        # Rule-based filter extraction for demonstration
        year = 2025 if "2025" in prompt else (2024 if "2024" in prompt else None)
        dept = "finance" if "margin" in prompt or "spend" in prompt else "engineering"
        return ExtractedFilters(fiscal_year=year, department=dept, confidentiality="internal")

# Verification
filters = MetadataFilterExtractor.extract_filters("What was our 2025 cloud infrastructure spend?")
print("Extracted Query Filters:", filters.model_dump())

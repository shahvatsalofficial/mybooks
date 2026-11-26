# custom_presidio_recognizer.py — Enterprise Custom PII Analyzer
import re
from typing import List, Optional
from presidio_analyzer import (
    Pattern,
    PatternRecognizer,
    RecognizerResult,
    AnalysisEngine,
    RecognizerRegistry
)

class EnterpriseBadgeRecognizer(PatternRecognizer):
    """Detects corporate employee badges: format EMP-XXXXXX-L (e.g. EMP-948102-A)."""
    PATTERNS = [
        Pattern(
            name="Employee_Badge_Pattern",
            regex=r"\bEMP-\d{6}-[A-Z]\b",
            score=0.75
        )
    ]
    CONTEXT = ["badge", "employee", "staff", "personnel", "worker", "contractor"]

    def __init__(self):
        super().__init__(
            supported_entity="ENTERPRISE_BADGE_ID",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language="en"
        )

    def validate_result(self, pattern_text: str) -> bool:
        # Checksum algorithm: sum of middle 6 digits must be even
        digits = [int(d) for d in re.findall(r'\d', pattern_text)]
        return sum(digits) % 2 == 0

class HealthcareMRNRecognizer(PatternRecognizer):
    """Detects Medical Record Numbers (MRN) adhering to HL7 hospital standards."""
    PATTERNS = [
        Pattern(
            name="Medical_Record_Number_Pattern",
            regex=r"\bMRN-\d{4}-\d{4}\b",
            score=0.60
        )
    ]
    CONTEXT = ["patient", "mrn", "medical record", "chart", "admit", "clinical"]

    def __init__(self):
        super().__init__(
            supported_entity="HEALTHCARE_MRN",
            patterns=self.PATTERNS,
            context=self.CONTEXT,
            supported_language="en"
        )

# Initialize Hardened Engine
def build_enterprise_analyzer() -> AnalysisEngine:
    registry = RecognizerRegistry()
    registry.load_predefined_recognizers()
    
    # Register custom enterprise recognizers
    registry.add_recognizer(EnterpriseBadgeRecognizer())
    registry.add_recognizer(HealthcareMRNRecognizer())
    
    engine = AnalysisEngine(registry=registry)
    return engine

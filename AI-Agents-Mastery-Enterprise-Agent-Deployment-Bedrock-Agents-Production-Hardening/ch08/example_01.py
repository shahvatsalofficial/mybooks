import json
from typing import Dict, Any, List
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

class PresidioPIISanitizationEngine:
    """Production PII detection and redaction engine using Microsoft Presidio."""

    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self._add_custom_enterprise_recognizers()

    def _add_custom_enterprise_recognizers(self):
        """Adds custom regex recognizers for proprietary employee badges and account IDs."""
        badge_pattern = Pattern(name="employee_badge_pattern", regex=r"\bEMP-[0-9]{5,7}\b", score=0.85)
        badge_recognizer = PatternRecognizer(
            supported_entity="ENTERPRISE_BADGE",
            patterns=[badge_pattern]
        )
        self.analyzer.registry.add_recognizer(badge_recognizer)

    def sanitize_text(self, text: str) -> Dict[str, Any]:
        """Scans and masks PII/PHI in unstructured text."""
        # 1. Analyze text for entities
        results = self.analyzer.analyze(
            text=text,
            language="en",
            entities=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN", "ENTERPRISE_BADGE"]
        )
        
        # 2. Anonymize detected entities with structured replacement tags
        operators = {
            "DEFAULT": OperatorConfig("replace", {"new_value": "[REDACTED]"}),
            "EMAIL_ADDRESS": OperatorConfig("mask", {"type": "mask", "masking_char": "*", "chars_to_mask": 5, "from_end": False}),
            "US_SSN": OperatorConfig("replace", {"new_value": "[REDACTED_SSN]"}),
            "ENTERPRISE_BADGE": OperatorConfig("replace", {"new_value": "[EMP_BADGE]"})
        }
        
        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators
        )
        
        detected_types = list(set([r.entity_type for r in results]))
        return {
            "clean_text": anonymized_result.text,
            "entities_found_count": len(results),
            "entity_types": detected_types
        }

if __name__ == "__main__":
    engine = PresidioPIISanitizationEngine()
    dirty_prompt = "Contact technician Alice Smith (EMP-99201) at alice.smith@corp.com or SSN 000-12-3456."
    print("Original text:\n", dirty_prompt)
    
    clean_res = engine.sanitize_text(dirty_prompt)
    print("\nSanitized text:\n", clean_res["clean_text"])
    print("Detected Entity Types:", clean_res["entity_types"])

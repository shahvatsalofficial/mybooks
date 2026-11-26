# custom_presidio_recognizers.py
from presidio_analyzer import Pattern, PatternRecognizer, AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

class EnterprisePIISanitizer:
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self._register_custom_patterns()

    def _register_custom_patterns(self):
        # 1. SWIFT / BIC Banking Code Pattern (8 or 11 characters)
        swift_pattern = Pattern(
            name="swift_bic_pattern",
            regex=r"[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?",
            score=0.85
        )
        swift_recognizer = PatternRecognizer(
            supported_entity="SWIFT_CODE",
            patterns=[swift_pattern],
            context=["swift", "bic", "wire transfer", "bank routing", "iban"]
        )
        self.analyzer.registry.add_recognizer(swift_recognizer)

        # 2. Corporate Global Employee ID (e.g., EMP-90482-X)
        egid_pattern = Pattern(
            name="egid_pattern",
            regex=r"EMP-d{5}-[A-Z]",
            score=0.95
        )
        egid_recognizer = PatternRecognizer(
            supported_entity="EMPLOYEE_ID",
            patterns=[egid_pattern],
            context=["employee", "staff id", "badge", "payroll", "personnel"]
        )
        self.analyzer.registry.add_recognizer(egid_recognizer)

    def sanitize_prompt(self, raw_text: str) -> dict:
        results = self.analyzer.analyze(text=raw_text, language="en")
        
        # Mask sensitive entities with synthetic tokens
        anonymized_result = self.anonymizer.anonymize(
            text=raw_text,
            analyzer_results=results,
            operators={
                "SWIFT_CODE": OperatorConfig("mask", {"masking_char": "*", "chars_to_mask": 6, "from_end": True}),
                "EMPLOYEE_ID": OperatorConfig("replace", {"new_value": "[REDACTED_EMP_ID]"}),
                "DEFAULT": OperatorConfig("replace", {"new_value": "[REDACTED]"})
            }
        )
        
        return {
            "clean_text": anonymized_result.text,
            "detected_entities": [r.entity_type for r in results]
        }

"""
banking_pii_recognizers.py
Enterprise Presidio Recognizers for Financial & Banking Identifiers
Implements ISO 13616 IBAN, ISO 9362 SWIFT/BIC, and ISO 6166 ISIN Detection
"""

from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern


def register_banking_recognizers(analyzer: AnalyzerEngine):
    # 1. International Bank Account Number (IBAN) Recognizer
    iban_regex = r"[A-Z]{2}[0-9]{2}[A-Z0-9]{4}[0-9]{7}([A-Z0-9]?){0,16}"
    iban_pattern = Pattern(name="iban_pattern", regex=iban_regex, score=0.90)
    iban_recognizer = PatternRecognizer(
        supported_entity="BANK_IBAN",
        patterns=[iban_pattern],
        context=["iban", "bank account", "transfer", "wire", "remittance"]
    )
    analyzer.registry.add_recognizer(iban_recognizer)

    # 2. SWIFT / BIC Code Recognizer (8 or 11 characters)
    swift_regex = r"[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?"
    swift_pattern = Pattern(name="swift_pattern", regex=swift_regex, score=0.85)
    swift_recognizer = PatternRecognizer(
        supported_entity="BANK_SWIFT_BIC",
        patterns=[swift_pattern],
        context=["swift", "bic", "routing code", "correspondent bank"]
    )
    analyzer.registry.add_recognizer(swift_recognizer)

    # 3. International Securities Identification Number (ISIN)
    isin_regex = r"[A-Z]{2}[A-Z0-9]{9}[0-9]"
    isin_pattern = Pattern(name="isin_pattern", regex=isin_regex, score=0.92)
    isin_recognizer = PatternRecognizer(
        supported_entity="FINANCIAL_ISIN",
        patterns=[isin_pattern],
        context=["isin", "securities", "bond", "equity", "cusip"]
    )
    analyzer.registry.add_recognizer(isin_recognizer)


if __name__ == "__main__":
    analyzer = AnalyzerEngine()
    register_banking_recognizers(analyzer)
    test_text = "Please initiate wire transfer of $1.5M to IBAN GB29XAAA10203012345678 via SWIFT CHASUS33XXX."
    results = analyzer.analyze(text=test_text, language="en")
    print(f"Detected {len(results)} banking PII entities:")
    for res in results:
        val = test_text[res.start:res.end]
        print(f" - [{res.entity_type}]: {val} (Confidence: {res.score})")

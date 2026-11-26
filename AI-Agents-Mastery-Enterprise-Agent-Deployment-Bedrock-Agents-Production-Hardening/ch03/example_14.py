import re

class PHIRedactionFilter:
    """Pre-egress filter scanning agent outputs for Protected Health Information."""
    
    SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
    MRN_REGEX = re.compile(r"\bMRN\d{7,10}\b")

    @classmethod
    def sanitize_output(cls, raw_text: str) -> str:
        sanitized = cls.SSN_REGEX.sub("[REDACTED_SSN]", raw_text)
        sanitized = cls.MRN_REGEX.sub("[REDACTED_MRN]", sanitized)
        return sanitized

if __name__ == "__main__":
    dirty_text = "Patient John Doe (SSN: 000-12-3456, MRN9821045) exhibits elevated systolic BP."
    clean_text = PHIRedactionFilter.sanitize_output(dirty_text)
    print("Sanitized Output:", clean_text)

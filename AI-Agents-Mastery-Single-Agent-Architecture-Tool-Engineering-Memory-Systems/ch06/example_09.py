class PIIRedactionPostprocessor:
    EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+.[a-zA-Z0-9-.]+")
    PHONE_REGEX = re.compile(r"d{3}[-.]?d{3}[-.]?d{4}")
    SSN_REGEX = re.compile(r"d{3}-d{2}-d{4}")

    @classmethod
    def redact(cls, text: str) -> str:
        s = cls.EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
        s = cls.PHONE_REGEX.sub("[REDACTED_PHONE]", s)
        s = cls.SSN_REGEX.sub("[REDACTED_SSN]", s)
        return s

# Verification
raw_chunk = "Customer Elena Rostova (elena@acme.corp, 415-555-0199, SSN 000-12-3456) reported billing discrepancy."
clean_chunk = PIIRedactionPostprocessor.redact(raw_chunk)
print("Sanitized Document Chunk:", clean_chunk)

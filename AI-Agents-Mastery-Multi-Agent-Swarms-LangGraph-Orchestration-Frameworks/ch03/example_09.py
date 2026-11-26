import re

class ContextFirewall:
    PII_PATTERNS = [
        (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[REDACTED_CREDIT_CARD]'),
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', '[REDACTED_EMAIL]'),
        (r'\bAKIA[0-9A-Z]{16}\b', '[REDACTED_AWS_KEY]')
    ]

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        sanitized = text
        for pattern, replacement in cls.PII_PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized)
        return sanitized

    @classmethod
    def sanitize_dictionary(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        clean_dict = {}
        for k, v in payload.items():
            if isinstance(v, str):
                clean_dict[k] = cls.sanitize_text(v)
            elif isinstance(v, list):
                clean_dict[k] = [cls.sanitize_text(item) if isinstance(item, str) else item for item in v]
            else:
                clean_dict[k] = v
        return clean_dict

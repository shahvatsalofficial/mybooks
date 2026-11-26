import re

def redact_sensitive_credentials(text_content: str) -> str:
    """Scrubs authorization headers, bearer tokens, and private keys from tool outputs."""
    # Redact Bearer Tokens
    scrubbed = re.sub(r"(Bearer\s+)[A-Za-z0-9\-\._~\+\/]+=*", r"\1[REDACTED_TOKEN]", text_content)
    # Redact AWS Access Keys
    scrubbed = re.sub(r"(AKIA[0-9A-Z]{16})", r"[REDACTED_AWS_KEY]", scrubbed)
    # Redact Generic Passwords in JSON
    scrubbed = re.sub(r'"(password|secret|api_key)":\s*"[^"]+"', r'"\1": "[REDACTED_SECRET]"', scrubbed)
    return scrubbed

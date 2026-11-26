import re
from urllib.parse import urlparse
from typing import Set

class MarkdownExfiltrationDefanger:
    def __init__(self, authorized_domains: Set[str]):
        self.authorized_domains = authorized_domains

    def sanitize_generated_markdown(self, raw_markdown: str) -> str:
        """
        Strips or defangs markdown images and external links to prevent data exfiltration.
        """
        # 1. Defang all markdown images: ![alt](url) -> [IMAGE REMOVED: alt]
        def defang_image(match: re.Match) -> str:
            alt_text = match.group(1)
            image_url = match.group(2)
            parsed = urlparse(image_url)
            
            # Check domain whitelist
            if parsed.netloc in self.authorized_domains:
                return match.group(0)  # Allowed
            
            return f"[DEFANGED_EXTERNAL_IMAGE: {alt_text}]"

        sanitized = re.sub(r"!\[(.*?)\]\((.*?)\)", defang_image, raw_markdown)

        # 2. Defang raw HTML img and script tags
        sanitized = re.sub(r"<(?:img|script|iframe)\b[^>]*>", "[DEFANGED_RAW_HTML_ELEMENT]", sanitized, flags=re.IGNORECASE)

        # 3. Defang suspicious exfiltration query strings in regular links
        # Flags links that contain more than 100 characters in query params
        def defang_suspicious_links(match: re.Match) -> str:
            link_text = match.group(1)
            url = match.group(2)
            parsed = urlparse(url)
            if len(parsed.query) > 60:
                return f"[SUSPICIOUS_LINK_BLOCKED: {link_text}]"
            return match.group(0)

        sanitized = re.sub(r"\[(.*?)\]\((.*?)\)", defang_suspicious_links, sanitized)

        return sanitized

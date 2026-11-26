import html
import re

class DelimiterSanitizer:
    # Reserved architectural tags used in enterprise system prompts
    RESERVED_TAGS = [
        "system", "instruction", "persona", "context",
        "scratchpad", "output", "internal_security_token", "user_input"
    ]

    @classmethod
    def sanitize_user_input(cls, raw_user_text: str) -> str:
        """
        Escapes reserved XML delimiters and neutralizing injection tags.
        """
        sanitized = raw_user_text

        # 1. Escape HTML/XML entities
        sanitized = html.escape(sanitized, quote=False)

        # 2. Defang any attempted reserved tag counterfeits
        for tag in cls.RESERVED_TAGS:
            # Defang <tag> and </tag>
            sanitized = re.sub(
                rf"&lt;(\/?\s*{tag}\s*)&gt;",
                r"[DEFANGED_\1]",
                sanitized,
                flags=re.IGNORECASE
            )

        # 3. Strip non-printable control characters that confuse tokenizers
        sanitized = "".join(ch for ch in sanitized if ch == "\n" or ch == "\t" or ord(ch) >= 32)

        return sanitized

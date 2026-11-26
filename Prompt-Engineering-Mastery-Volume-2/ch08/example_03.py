import re
import json
from typing import Dict, Any, Optional

class DeterministicJSONSanitizer:
    @staticmethod
    def sanitize(raw_text: str) -> Dict[str, Any]:
        """Cleans and extracts JSON objects from raw text emissions."""
        # 1. Strip markdown fences
        text = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
        text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)

        # 2. Extract outermost JSON object or array
        match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if match:
            text = match.group(1).strip()

        # 3. Clean up common JSON anti-patterns
        # Replace Python boolean strings with standard JSON
        text = re.sub(r"\bTrue\b", "true", text)
        text = re.sub(r"\bFalse\b", "false", text)
        text = re.sub(r"\bNone\b", "null", text)

        # Strip illegal trailing commas before closing curly braces or brackets
        text = re.sub(r",\s*(\}|\])", r"\1", text)

        # Attempt immediate fast-parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 4. Fallback: replace unescaped internal newlines within string values
        text_cleaned = re.sub(r'(?<!\\)\n', r'\\n', text)
        return json.loads(text_cleaned)

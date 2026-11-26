class AutoHealingJSONParser:
    @staticmethod
    def parse_and_repair(raw_text: str) -> Dict[str, Any]:
        cleaned = raw_text.strip()
        # Strip markdown fences if present
        cleaned = re.sub(r"^```(?:json)?s*", "", cleaned)
        cleaned = re.sub(r"s*```$", "", cleaned)
        
        # Remove trailing commas before closing braces
        cleaned = re.sub(r",s*([]}])", r"\1", cleaned)
        
        # Ensure closing brace if truncated
        if cleaned.startswith("{") and not cleaned.endswith("}"):
            cleaned += "}"
            
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(f"Irreparable JSON payload: '{raw_text}'") from e

# Verification
bad_json = '{
  "status": "success",
  "code": 200,
}'
repaired = AutoHealingJSONParser.parse_and_repair(bad_json)
print("Repaired JSON Object:", repaired)

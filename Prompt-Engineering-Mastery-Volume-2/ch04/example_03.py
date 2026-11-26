import json
from typing import Dict, Any

class ObservationGovernor:
    def __init__(self, max_tokens_estimate: int = 800):
        self.char_ceiling = max_tokens_estimate * 4

    def sanitize_and_govern(self, raw_output: str) -> str:
        """Truncates and extracts high-signal keys from verbose tool responses."""
        if len(raw_output) <= self.char_ceiling:
            return raw_output

        # Try parsing as JSON to execute surgical structural compression
        try:
            data = json.loads(raw_output)
            if isinstance(data, list):
                # Sample top 3 items and include total count indicator
                sample = data[:3]
                compressed = {
                    "total_records": len(data),
                    "sampled_records": sample,
                    "note": f"Truncated {len(data) - 3} additional records to preserve context window."
                }
                return json.dumps(compressed, indent=2)
            elif isinstance(data, dict):
                # Strip nulls and giant base64 or blob fields
                pruned = {
                    k: v for k, v in data.items()
                    if v is not None and not (isinstance(v, str) and len(v) > 500)
                }
                pruned_str = json.dumps(pruned)
                if len(pruned_str) <= self.char_ceiling:
                    return pruned_str
        except Exception:
            pass

        # Raw string fallback truncation
        half = self.char_ceiling // 2
        return (
            raw_output[:half] +
            f"\n\n[... TRUNCATED {len(raw_output) - self.char_ceiling} CHARACTERS DUE TO GOVERNOR CEILING ...] \n\n" +
            raw_output[-half:]
        )

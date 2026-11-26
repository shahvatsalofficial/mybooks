class RobustJSONRepair:
    @staticmethod
    def repair(broken_json: str) -> str:
        s = broken_json.strip()
        # Convert single quotes to double quotes
        s = re.sub(r"(?<!\\)'", r'"', s)
        # Quote unquoted keys: e.g. {action: "run"} -> {"action": "run"}
        s = re.sub(r'([{,]s*)([a-zA-Z_][a-zA-Z0-9_]*)s*:', r'\1"\2":', s)
        # Remove trailing commas
        s = re.sub(r',s*([]}])', r'\1', s)
        # Balance brackets if truncated
        open_braces = s.count('{') - s.count('}')
        if open_braces > 0:
            s += '}' * open_braces
        return s

# Verification
malformed = "{action: 'query', id: 42,}"
repaired = RobustJSONRepair.repair(malformed)
print("Repaired JSON:", repaired)
print("Parsed OK:", json.loads(repaired))

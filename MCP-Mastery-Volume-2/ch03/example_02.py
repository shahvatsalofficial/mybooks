# CATASTROPHIC ANTI-PATTERN: DO NOT RELY ON REGEX FOR SQL SANITIZATION
if "DROP" in query.upper() or "DELETE" in query.upper():
    raise ValueError("Dangerous query detected!")

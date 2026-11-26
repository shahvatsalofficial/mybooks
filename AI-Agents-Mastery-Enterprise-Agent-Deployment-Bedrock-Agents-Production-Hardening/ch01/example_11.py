import re
from typing import Dict, Any, Tuple

class ActionGroupInputValidator:
    """Pre-execution validation guardrail for Action Group parameters."""

    LOG_GROUP_PATTERN = re.compile(r"^/aws/(ecs|lambda|rds|eks)/[a-zA-Z0-9_-]+$")

    @classmethod
    def validate_query_logs_input(cls, params: Dict[str, Any]) -> Tuple[bool, str]:
        log_group = params.get("log_group", "")
        query = params.get("query_string", "")
        
        if not cls.LOG_GROUP_PATTERN.match(log_group):
            return False, f"Invalid log_group format: '{log_group}'. Must match /aws/<service>/<name>."
        if "drop" in query.lower() or "delete" in query.lower():
            return False, "Query string contains prohibited destructive keywords."
        return True, "Valid"

if __name__ == "__main__":
    valid, msg = ActionGroupInputValidator.validate_query_logs_input({
        "log_group": "/aws/ecs/payment-service",
        "query_string": "fields @timestamp | limit 10"
    })
    print(f"-> Parameter Validation Result: {valid} ({msg})")

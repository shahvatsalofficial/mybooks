from typing import Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict, ValidationError

class EnterpriseDatabaseQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    table_name: str = Field(..., pattern=r"^[a-zA-Z_][a-zA-Z0-9_]{1,63}$")
    limit: int = Field(default=50, ge=1, le=1000)
    filter_keys: List[str] = Field(default_factory=list, max_length=10)

def validate_and_gate_tool_call(raw_arguments: Dict[str, Any]) -> EnterpriseDatabaseQuery:
    try:
        validated = EnterpriseDatabaseQuery.model_validate(raw_arguments)
        print(f"[SCHEMA GATE] Validation PASSED for table: '{validated.table_name}'")
        return validated
    except ValidationError as e:
        print("[SCHEMA GATE] Validation REJECTED with structural errors:")
        for err in e.errors():
            print(f"  - Field '{err['loc']}': {err['msg']} (Input: {err.get('input')})")
        raise

valid_payload = {"table_name": "customer_invoices", "limit": 100}
query = validate_and_gate_tool_call(valid_payload)

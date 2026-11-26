import json
import time
from typing import Dict, Any, Tuple
from pydantic import BaseModel, Field

class SchemaDefinition(BaseModel):
    schema_id: str
    version: int
    raw_json_schema: Dict[str, Any]
    registered_at: float = Field(default_factory=time.time)

class DynamicSchemaRegistryGateway:
    """Manages cached JSON-Schema contracts with zero-downtime hot reloading."""
    
    def __init__(self):
        self.cached_schemas: Dict[str, SchemaDefinition] = {}
        self.validation_errors_count: int = 0

    def register_or_update_schema(self, schema_id: str, version: int, schema_dict: Dict[str, Any]) -> None:
        self.cached_schemas[schema_id] = SchemaDefinition(
            schema_id=schema_id,
            version=version,
            raw_json_schema=schema_dict
        )
        print(f"[SCHEMA REGISTRY] Pinned schema '{schema_id}' updated to v{version} (hot-reloaded).")

    def validate_payload(self, schema_id: str, payload: Dict[str, Any]) -> Tuple[bool, str]:
        schema_def = self.cached_schemas.get(schema_id)
        if not schema_def:
            return False, f"UNKNOWN_SCHEMA: No contract registered for '{schema_id}'."
            
        required_fields = schema_def.raw_json_schema.get("required", [])
        missing = [f for f in required_fields if f not in payload]
        
        if missing:
            self.validation_errors_count += 1
            err_msg = f"SCHEMA_BREACH: Missing mandatory contract fields: {missing}"
            print(f"[VALIDATION REJECTION] {err_msg} on schema '{schema_id}' v{schema_def.version}")
            return False, err_msg
            
        print(f"[VALIDATION PASS] Envelope conforms to '{schema_id}' v{schema_def.version} contract.")
        return True, "VALIDATION_SUCCESS"

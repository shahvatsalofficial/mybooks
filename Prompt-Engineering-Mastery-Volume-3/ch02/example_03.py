# tool_registry.py
import inspect
from typing import Callable, Dict, Any, List
from pydantic import BaseModel, create_model

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: List[Dict[str, Any]] = []

    def register(self, name: str, description: str):
        def decorator(func: Callable):
            sig = inspect.signature(func)
            fields = {}
            for param_name, param in sig.parameters.items():
                annotation = param.annotation if param.annotation != inspect.Parameter.empty else str
                default_val = ... if param.default == inspect.Parameter.empty else param.default
                fields[param_name] = (annotation, default_val)

            # Compile dynamic Pydantic model to generate standard JSON Schema
            schema_model = create_model(f"{name}_schema", **fields)
            json_schema = schema_model.model_json_schema()
            
            tool_spec = {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description.strip(),
                    "parameters": {
                        "type": "object",
                        "properties": json_schema.get("properties", {}),
                        "required": json_schema.get("required", []),
                        "additionalProperties": False
                    }
                }
            }
            self._tools[name] = func
            self._schemas.append(tool_spec)
            return func
        return decorator

    def get_schemas(self) -> List[Dict[str, Any]]:
        return self._schemas

    def execute(self, name: str, args: Dict[str, Any]) -> Any:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered.")
        return self._tools[name](**args)

import inspect
import json
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, get_type_hints
from pydantic import BaseModel, ConfigDict, Field, ValidationError, create_model

class ToolExecutionResult(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0

class EnterpriseToolGateway:
    def __init__(self):
        self._registry: Dict[str, Tuple[Callable, Type[BaseModel], str]] = {}

    def register(self, name: Optional[str] = None, description: Optional[str] = None):
        def decorator(func: Callable):
            tool_name = name or func.__name__
            docstring = description or inspect.getdoc(func) or "No description provided."
            
            sig = inspect.signature(func)
            hints = get_type_hints(func)
            
            fields = {}
            for param_name, param in sig.parameters.items():
                if param_name in ('self', 'cls'):
                    continue
                param_type = hints.get(param_name, Any)
                if param.default is inspect.Parameter.empty:
                    fields[param_name] = (param_type, ...)
                else:
                    fields[param_name] = (param_type, param.default)
            
            # Configure Pydantic model with loose type coercion to tolerate model quirks
            model = create_model(
                f"{tool_name}_InputSchema",
                __config__=ConfigDict(str_strip_whitespace=True, coerce_numbers_to_str=False),
                **fields
            )
            
            self._registry[tool_name] = (func, model, docstring)
            return func
        return decorator

    def get_openai_tool_specs(self) -> List[Dict[str, Any]]:
        specs = []
        for name, (_, model, desc) in self._registry.items():
            schema = model.model_json_schema()
            specs.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": desc,
                    "parameters": {
                        "type": "object",
                        "properties": schema.get("properties", {}),
                        "required": schema.get("required", [])
                    }
                }
            })
        return specs

    def dispatch(self, tool_name: str, arguments: Dict[str, Any]) -> ToolExecutionResult:
        if tool_name not in self._registry:
            return ToolExecutionResult(success=False, error=f"Tool '{tool_name}' not found.")
        
        func, model_cls, _ = self._registry[tool_name]
        try:
            validated = model_cls(**arguments)
            raw_output = func(**validated.model_dump())
            return ToolExecutionResult(success=True, data=raw_output)
        except ValidationError as val_err:
            return ToolExecutionResult(
                success=False, 
                error=f"Schema Validation Error: {val_err.json()}"
            )
        except Exception as exec_err:
            return ToolExecutionResult(success=False, error=f"Internal Runtime Exception: {str(exec_err)}")

# Verification
gateway = EnterpriseToolGateway()

@gateway.register(description="Calculate corporate discount based on tier and volume.")
def calculate_discount(tier: str, volume_units: int, is_nonprofit: bool = False) -> Dict[str, Any]:
    base_rate = 0.15 if tier.lower() == "enterprise" else 0.05
    if volume_units > 1000:
        base_rate += 0.05
    if is_nonprofit:
        base_rate += 0.10
    return {"effective_discount_rate": round(base_rate, 4), "tier": tier}

# Model emitted volume_units as string "5000" instead of int 5000
test_payload = {"tier": "enterprise", "volume_units": "5000", "is_nonprofit": False}
res = gateway.dispatch("calculate_discount", test_payload)
print(f"Dispatch Status: {res.success}")
print(f"Calculated Data: {res.data}")

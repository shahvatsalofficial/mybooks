import inspect
from typing import get_type_hints
from pydantic import create_model

class ProductionToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._executors: Dict[str, Tuple[Callable, type[BaseModel]]] = {}

    def register(self, name: Optional[str] = None, description: Optional[str] = None):
        def decorator(func: Callable):
            tool_name = name or func.__name__
            docstring = description or inspect.getdoc(func) or "No description provided."
            
            sig = inspect.signature(func)
            hints = get_type_hints(func)
            
            field_definitions = {}
            for param_name, param in sig.parameters.items():
                if param_name in ('self', 'cls'):
                    continue
                param_type = hints.get(param_name, Any)
                if param.default is inspect.Parameter.empty:
                    field_definitions[param_name] = (param_type, ...)
                else:
                    field_definitions[param_name] = (param_type, param.default)
            
            pydantic_model = create_model(f"{tool_name}_ArgsModel", **field_definitions)
            json_schema = pydantic_model.model_json_schema()
            
            tool_spec = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": docstring,
                    "parameters": {
                        "type": "object",
                        "properties": json_schema.get("properties", {}),
                        "required": json_schema.get("required", [])
                    }
                }
            }
            
            self._tools[tool_name] = tool_spec
            self._executors[tool_name] = (func, pydantic_model)
            return func
        return decorator

    def get_tool_specs(self) -> List[Dict[str, Any]]:
        return list(self._tools.values())

    def invoke(self, name: str, arguments: Dict[str, Any]) -> Any:
        if name not in self._executors:
            raise KeyError(f"Tool '{name}' is not registered.")
        
        func, model_cls = self._executors[name]
        validated_instance = model_cls(**arguments)
        return func(**validated_instance.model_dump())

# Verification of Recipe 1.2
registry = ProductionToolRegistry()

@registry.register(description="Perform vector cosine similarity search over incident archives.")
def search_incident_vault(query: str, top_k: int = 5, min_score: float = 0.82) -> List[str]:
    return [f"Incident report for query: '{query}' (Rank 1, Score {min_score})"]

print("Generated OpenAI/Anthropic Tool Spec:")
print(json.dumps(registry.get_tool_specs(), indent=2))

from typing import Dict, Any, Type
from pydantic import BaseModel, Field

class ClusterStatusQuery(BaseModel):
    cluster_id: str = Field(..., description="Unique K8s cluster identifier")
    namespace: str = Field(default="production")
    include_metrics: bool = Field(default=True)

class DynamicToolMockFactory:
    @staticmethod
    def generate_mock_response(schema_cls: Type[BaseModel]) -> Dict[str, Any]:
        schema = schema_cls.model_json_schema()
        mock_data = {}
        for prop_name, prop_meta in schema.get("properties", {}).items():
            p_type = prop_meta.get("type", "string")
            if p_type == "string":
                mock_data[prop_name] = f"mock_{prop_name}_value"
            elif p_type == "integer":
                mock_data[prop_name] = 42
            elif p_type == "boolean":
                mock_data[prop_name] = True
        return {"mock_status": "MOCK_SUCCESS", "payload": mock_data}

mock = DynamicToolMockFactory.generate_mock_response(ClusterStatusQuery)
print("Synthesized Dynamic Tool Mock:", mock)

import json
from typing import Dict, Any
from anthropic import Anthropic

class ClaudeStructuredOutputEngine:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)

    def extract_structured_data(
        self,
        user_input: str,
        schema_model: type[BaseModel],
        tool_name: str = "emit_structured_data"
    ) -> BaseModel:
        # Convert Pydantic schema to Anthropic tool parameter definition
        tool_def = {
            "name": tool_name,
            "description": "Emits deterministic structured data conforming strictly to the enterprise schema.",
            "input_schema": schema_model.model_json_schema()
        }

        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            temperature=0.0,
            tools=[tool_def],
            tool_choice={"type": "tool", "name": tool_name},  # Forces model to invoke this exact tool
            messages=[{"role": "user", "content": user_input}]
        )

        # Extract tool input payload
        for content_block in response.content:
            if content_block.type == "tool_use" and content_block.name == tool_name:
                raw_json_dict = content_block.input
                # Validate and hydrate into target Pydantic instance
                return schema_model.model_validate(raw_json_dict)

        raise RuntimeError("Model failed to invoke mandated structured tool.")

import os
from typing import Any, Dict, List
from autogen import AssistantAgent, UserProxyAgent, config_list_from_json

# Configure LLM endpoints (OpenAI / Azure / Local vLLM)
llm_config = {
    "config_list": [
        {
            "model": "gpt-4o",
            "api_key": os.getenv("OPENAI_API_KEY", "mock-key-for-local-verification"),
            "temperature": 0.0 # Deterministic code generation
        }
    ],
    "timeout": 120,
    "cache_seed": 42 # Deterministic caching of LLM calls
}

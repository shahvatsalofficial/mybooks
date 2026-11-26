from typing import Dict, Any, List
from anthropic import Anthropic

class CachedEnterpriseKnowledgeEngine:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)

    def query_with_cached_knowledge_base(
        self,
        large_static_kb_text: str,
        user_query: str
    ) -> Dict[str, Any]:
        """
        Marks large static documentation with ephemeral cache_control,
        allowing high-speed, 90% discounted KV-cache reuse.
        """
        response = self.client.beta.prompt_caching.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            system=[
                {
                    "type": "text",
                    "text": "You are a Principal Technical Solutions Architect specializing in enterprise cloud migrations."
                },
                {
                    "type": "text",
                    "text": f"ENTERPRISE ARCHITECTURE REPOSITORY:\n{large_static_kb_text}",
                    "cache_control": {"type": "ephemeral"}  # Persists KV cache for 5 minutes
                }
            ],
            messages=[
                {"role": "user", "content": user_query}
            ]
        )

        usage = response.usage
        return {
            "reply": response.content[0].text,
            "input_tokens": usage.input_tokens,
            "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", 0),
            "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", 0),
            "cache_hit": getattr(usage, "cache_read_input_tokens", 0) > 0
        }

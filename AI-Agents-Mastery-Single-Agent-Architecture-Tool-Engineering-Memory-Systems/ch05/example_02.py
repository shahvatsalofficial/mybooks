import os
from typing import Any, Dict, List
from pydantic import BaseModel, Field

# Mocking modern LangChain 0.3 interfaces for demonstration and zero-dependency verification
class MockChatPromptTemplate:
    def __init__(self, messages: List[Tuple[str, str]]):
        self.messages = messages

    def format_messages(self, **kwargs) -> List[Dict[str, str]]:
        formatted = []
        for role, text in self.messages:
            for k, v in kwargs.items():
                text = text.replace(f"{{{k}}}", str(v))
            formatted.append({"role": role, "content": text})
        return formatted

class MockToolCallingModel:
    def __init__(self, provider: str = "anthropic"):
        self.provider = provider
        self.bound_tools: List[Dict[str, Any]] = []

    def bind_tools(self, tools: List[Any]):
        self.bound_tools = tools
        return self

    def invoke(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        # Emulate native function calling response
        return {
            "role": "assistant",
            "content": "",
            "tool_calls": [{
                "id": "call_991",
                "name": "lookup_account_tier",
                "args": {"account_id": "ACC-781"}
            }]
        }

# Define Pydantic Tool Schemas
class AccountLookupInput(BaseModel):
    account_id: str = Field(description="Unique enterprise account identifier (e.g. ACC-781)")

def lookup_account_tier(account_id: str) -> str:
    """Query operational CRM for enterprise service level agreements."""
    if account_id == "ACC-781":
        return json.dumps({"tier": "Platinum", "dedicated_rep": "Marcus Chen", "sla_hours": 1})
    return json.dumps({"tier": "Standard", "sla_hours": 24})

# Build LCEL Agent
prompt = MockChatPromptTemplate([
    ("system", "You are an enterprise SLA enforcement agent. Always verify account tier before escalation."),
    ("user", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

model = MockToolCallingModel(provider="anthropic").bind_tools([lookup_account_tier])
messages = prompt.format_messages(input="Customer ACC-781 reported an outage. What is their SLA tier?")
response = model.invoke(messages)

print("Agent Invocation Result:")
print(json.dumps(response, indent=2))

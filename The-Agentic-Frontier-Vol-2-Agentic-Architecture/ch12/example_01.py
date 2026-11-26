# mock_llm_stub.py
"""
Deterministic Mock LLM Stub for Agent Integration Testing
Implements the LangChain BaseChatModel interface for drop-in replacement.
"""
import hashlib
import json
from typing import Any, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class MockLLMStub(BaseChatModel):
    """
    A deterministic LLM stub for CI testing.
    Returns fixture responses keyed by a SHA-256 hash of input messages.
    Falls back to a configurable default response if no match is found.
    """
    fixture_responses: dict = {}
    default_response: str = "I cannot answer that in test mode."
    call_log: List[dict] = []

    def _hash_messages(self, messages: List[BaseMessage]) -> str:
        """Generates a stable hash from the serialized message list."""
        serialized = json.dumps(
            [{"role": m.type, "content": m.content} for m in messages],
            sort_keys=True
        )
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any
    ) -> ChatResult:
        """Core generation method — returns fixture or default response."""
        msg_hash = self._hash_messages(messages)
        response_content = self.fixture_responses.get(
            msg_hash,
            self.default_response
        )

        # Log every call for assertion in tests
        self.call_log.append({
            "hash": msg_hash,
            "matched_fixture": msg_hash in self.fixture_responses,
            "response": response_content
        })

        return ChatResult(generations=[
            ChatGeneration(message=AIMessage(content=response_content))
        ])

    @property
    def _llm_type(self) -> str:
        return "mock_llm_stub"


# ─── Test Fixture Factory ────────────────────────────────────────────────────

def build_fixtures_from_golden_dataset(dataset_path: str) -> dict:
    """
    Loads a golden dataset JSONL file and creates the fixture hash map.

    Golden dataset format (JSONL):
    {"messages": [{"role": "user", "content": "What is 2+2?"}],
     "expected_response": "The answer is 4."}
    """
    fixtures = {}
    stub = MockLLMStub()

    with open(dataset_path, "r") as f:
        for line in f:
            record = json.loads(line.strip())
            messages_raw = record["messages"]
            # Re-hydrate into LangChain message objects for hashing
            from langchain_core.messages import HumanMessage, SystemMessage
            messages = []
            for m in messages_raw:
                if m["role"] == "user":
                    messages.append(HumanMessage(content=m["content"]))
                elif m["role"] == "system":
                    messages.append(SystemMessage(content=m["content"]))

            msg_hash = stub._hash_messages(messages)
            fixtures[msg_hash] = record["expected_response"]

    return fixtures

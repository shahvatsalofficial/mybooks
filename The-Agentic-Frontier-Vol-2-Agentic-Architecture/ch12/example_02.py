# test_agent_orchestration.py
import pytest
from unittest.mock import patch, MagicMock
from your_agent.agent import ResearchAgent
from tests.mocks.mock_llm_stub import MockLLMStub


@pytest.fixture
def mock_llm():
    """Provides a configured Mock LLM stub with pre-loaded fixtures."""
    stub = MockLLMStub(
        fixture_responses={
            # Hash of: [SystemMessage(...), HumanMessage("Summarize AI trends 2025")]
            "a3f7b291c84e1d20": "Based on my research, the three dominant AI trends of 2025 are: (1) Multi-agent orchestration frameworks...",
            # Hash of: error scenario — empty user message
            "c10d4e8a92f73b15": "I need a specific question to help you effectively.",
        },
        default_response="FIXTURE_MISSING: Update golden dataset."
    )
    return stub


@pytest.fixture
def agent(mock_llm):
    """Creates a ResearchAgent instance with the mock LLM injected."""
    return ResearchAgent(
        llm=mock_llm,
        tools=[],  # No real tools needed for orchestration tests
        max_iterations=5
    )


class TestAgentOrchestration:
    def test_returns_structured_summary_for_valid_query(self, agent, mock_llm):
        """Verifies the agent correctly wraps LLM output in a structured response."""
        result = agent.run("Summarize AI trends 2025")
        assert result.status == "success"
        assert "Multi-agent orchestration" in result.content
        assert len(mock_llm.call_log) == 1
        assert mock_llm.call_log[0]["matched_fixture"] is True

    def test_handles_empty_input_gracefully(self, agent, mock_llm):
        """Verifies the agent handles empty user messages without crashing."""
        result = agent.run("")
        assert result.status in ["success", "clarification_needed"]
        assert result.content is not None

    def test_respects_max_iterations_limit(self, agent, mock_llm):
        """Verifies the agent terminates after max_iterations even without LLM answer."""
        agent.max_iterations = 2
        # Force the mock to return a response that keeps the agent looping
        mock_llm.default_response = "Action: search\nAction Input: more information"
        result = agent.run("An unanswerable recursive query")
        assert result.status in ["max_iterations_reached", "error"]
        assert len(mock_llm.call_log) <= 2

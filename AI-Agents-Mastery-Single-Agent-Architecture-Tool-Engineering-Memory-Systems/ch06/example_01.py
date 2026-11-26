import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# Mocking LlamaIndex 0.11+ Core Abstractions for zero-dependency verification
class MockDocumentIndex:
    def __init__(self, name: str, corpus: Dict[str, str]):
        self.name = name
        self.corpus = corpus

    def query(self, query_str: str) -> str:
        # Search corpus for matching keywords
        for k, text in self.corpus.items():
            if any(term in text.lower() for term in query_str.lower().split()):
                return f"[{self.name} Match]: {text}"
        return f"[{self.name}]: No conclusive records found for query '{query_str}'."

class QueryEngineTool:
    def __init__(self, name: str, description: str, index: MockDocumentIndex):
        self.name = name
        self.description = description
        self.index = index

    def execute(self, query: str) -> str:
        return self.index.query(query)

    def to_tool_spec(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Specific search query"}
                    },
                    "required": ["query"]
                }
            }
        }

# 1. Initialize Heterogeneous Indexes
sec_index = MockDocumentIndex(
    name="SEC_Filings",
    corpus={"acme_2025": "Acme Corp 2025 Gross Margin: 34.2%. Reported cloud spend: $14.2M on AWS."}
)
eng_index = MockDocumentIndex(
    name="Architecture_Docs",
    corpus={"k8s_infra": "Acme engineering runs 45 Kubernetes clusters across us-east-1 and eu-central-1."}
)

# 2. Wrap as Tools
tool_sec = QueryEngineTool(
    name="query_sec_filings",
    description="Search audited annual 10-K financial filings and risk reports.",
    index=sec_index
)
tool_eng = QueryEngineTool(
    name="query_engineering_docs",
    description="Search internal cloud infrastructure topology and system designs.",
    index=eng_index
)

# 3. Simulate Agent Execution
class MockFunctionCallingAgent:
    def __init__(self, tools: List[QueryEngineTool]):
        self.tools = {t.name: t for t in tools}

    def chat(self, prompt: str) -> str:
        # Step 1: Agent decides which tools to call
        obs1 = self.tools["query_sec_filings"].execute("gross margin cloud spend")
        obs2 = self.tools["query_engineering_docs"].execute("kubernetes clusters")
        
        # Step 2: Synthesis
        return (
            f"Synthesized Findings:\n"
            f"1. Financials: {obs1}\n"
            f"2. Infrastructure: {obs2}\n"
            f"Conclusion: Acme Corp's $14.2M cloud budget directly funds their 45-cluster Kubernetes deployment."
        )

# Verification
agent = MockFunctionCallingAgent(tools=[tool_sec, tool_eng])
response = agent.chat("What is Acme's cloud spend and how is their infrastructure deployed?")
print(response)

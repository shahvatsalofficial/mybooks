import os
import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# Enable native LangSmith distributed tracing
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY", "mock-langsmith-key-for-local-audit")
os.environ["LANGCHAIN_PROJECT"] = "enterprise-multiagent-swarm-prod"

print(f"[LANGSMITH CONFIG] Tracing enabled for project: '{os.environ['LANGCHAIN_PROJECT']}'")

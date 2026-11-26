import os
import sys
import json
import uuid
from typing import Dict, Any, Generator
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

class BedrockAgentRuntimeClient:
    """Production runtime client for AWS Bedrock Agents using streaming response parsing."""
    
    def __init__(self, region_name: str = "us-east-1"):
        boto_config = Config(
            region_name=region_name,
            retries={"max_attempts": 5, "mode": "adaptive"},
            connect_timeout=10,
            read_timeout=60
        )
        self.client = boto3.client("bedrock-agent-runtime", config=boto_config)
        self.session_id = str(uuid.uuid4())

    def invoke_agent_stream(
        self,
        agent_id: str,
        agent_alias_id: str,
        input_text: str,
        enable_trace: bool = True
    ) -> Generator[Dict[str, Any], None, None]:
        """Dispatches an intent to the Bedrock Agent and streams back text chunks and trace events."""
        try:
            response = self.client.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                sessionId=self.session_id,
                inputText=input_text,
                enableTrace=enable_trace,
                endSession=False
            )
            event_stream = response.get("completion")
            for event in event_stream:
                if "chunk" in event:
                    raw_bytes = event["chunk"].get("bytes", b"")
                    yield {"type": "chunk", "text": raw_bytes.decode("utf-8")}
                elif "trace" in event and enable_trace:
                    yield {"type": "trace", "data": event["trace"]}
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_msg = e.response["Error"]["Message"]
            yield {"type": "error", "code": error_code, "message": error_msg}

# Verification Execution Harness
if __name__ == "__main__":
    print("--- INITIATING BEDROCK AGENT STREAMING HARNESS ---")
    runtime = BedrockAgentRuntimeClient(region_name="us-east-1")
    print(f"-> Session Initialized: {runtime.session_id}")
    print("-> Ready for Agent Dispatch (Action Groups & Knowledge Base Ready)")

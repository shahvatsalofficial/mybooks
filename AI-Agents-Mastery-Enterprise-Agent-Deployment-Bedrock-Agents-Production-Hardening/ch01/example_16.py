import os
import boto3
from typing import Dict, Any
from botocore.config import Config

class CrossAccountActionGroupBroker:
    """Assumes scoped IAM roles in target production AWS accounts for tool execution."""

    def __init__(self, target_role_arn: str, external_id: str, session_duration_seconds: int = 900):
        self.target_role_arn = target_role_arn
        self.external_id = external_id
        self.duration = session_duration_seconds
        self.sts_client = boto3.client('sts', config=Config(retries={'max_attempts': 3, 'mode': 'adaptive'}))

    def obtain_target_session(self, tool_execution_id: str) -> boto3.Session:
        """Assumes role with strict external ID and session tagging."""
        response = self.sts_client.assume_role(
            RoleArn=self.target_role_arn,
            RoleSessionName=f"BedrockTool-{tool_execution_id[:16]}",
            ExternalId=self.external_id,
            DurationSeconds=self.duration
        )
        credentials = response['Credentials']
        return boto3.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken']
        )

if __name__ == '__main__':
    broker = CrossAccountActionGroupBroker(
        target_role_arn="arn:aws:iam::112233445566:role/ProductionDatabaseToolExecutor",
        external_id="enterprise-bedrock-ext-901"
    )
    print("CrossAccountActionGroupBroker initialized successfully.")

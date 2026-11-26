import json
from typing import Dict, Any

class BedrockIAMPolicyGenerator:
    """Generates hardened least-privilege IAM policies for Bedrock Agents."""

    @staticmethod
    def generate_agent_trust_policy() -> Dict[str, Any]:
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "BedrockAgentTrust",
                    "Effect": "Allow",
                    "Principal": {"Service": "bedrock.amazonaws.com"},
                    "Action": "sts:AssumeRole",
                    "Condition": {
                        "StringEquals": {"aws:SourceAccount": "123456789012"},
                        "ArnLike": {"aws:SourceArn": "arn:aws:bedrock:us-east-1:123456789012:agent/*"}
                    }
                }
            ]
        }

    @staticmethod
    def generate_action_group_invoke_policy(lambda_arn: str) -> Dict[str, Any]:
        return {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "InvokeLambdaActionGroup",
                    "Effect": "Allow",
                    "Action": "lambda:InvokeFunction",
                    "Resource": lambda_arn
                }
            ]
        }

if __name__ == "__main__":
    trust = BedrockIAMPolicyGenerator.generate_agent_trust_policy()
    print("-> IAM Trust Policy Configured with Strict Account Boundary:")
    print(f"   Principal: {trust['Statement'][0]['Principal']['Service']}")

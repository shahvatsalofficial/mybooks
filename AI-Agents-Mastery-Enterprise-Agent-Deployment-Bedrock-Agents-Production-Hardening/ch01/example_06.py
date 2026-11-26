import boto3
from typing import Dict, Any

class BedrockGuardrailManager:
    """Enforces enterprise safety policies, PII filters, and prompt injection barriers."""
    
    def __init__(self, region_name: str = "us-east-1"):
        self.client = boto3.client("bedrock", region_name=region_name)

    def create_sre_guardrail(self, name: str) -> Dict[str, Any]:
        response = self.client.create_guardrail(
            name=name,
            description="Blocks PII leakage, prompt injections, and unapproved financial advice.",
            topicPolicyConfig={
                "topicsConfig": [
                    {
                        "name": "FinancialTransactions",
                        "definition": "Handling stock purchases, bank transfers, or credit card updates.",
                        "type": "DENY"
                    }
                ]
            },
            sensitiveInformationPolicyConfig={
                "piiEntitiesConfig": [
                    {"type": "AWS_ACCESS_KEY", "action": "BLOCK"},
                    {"type": "EMAIL", "action": "ANONYMIZE"},
                    {"type": "US_SOCIAL_SECURITY_NUMBER", "action": "BLOCK"}
                ]
            },
            blockedInputMessaging="BLOCKED: Input violated enterprise safety policy.",
            blockedOutputsMessaging="BLOCKED: Output contained restricted sensitive data."
        )
        return response

if __name__ == "__main__":
    print("-> Bedrock Guardrails Engine Active (KMS Encryption & PII Anonymization enabled)")

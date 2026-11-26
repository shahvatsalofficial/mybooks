import boto3
from typing import Dict, Any

class BedrockGuardrailAlertingEngine:
    """Provisions CloudWatch metric alarms for Bedrock Guardrail interventions."""

    def __init__(self, region_name: str = 'us-east-1'):
        self.cw = boto3.client('cloudwatch', region_name=region_name)

    def provision_injection_alarm(self, guardrail_id: str, sns_topic_arn: str) -> Dict[str, Any]:
        """Creates an alarm triggering when prompt injection blocks exceed 5 in a 5-minute window."""
        alarm_name = f"Bedrock-PromptInjection-High-{guardrail_id}"
        self.cw.put_metric_alarm(
            AlarmName=alarm_name,
            AlarmDescription="Alerts on high volume of prompt injection blocks in AWS Bedrock Agent",
            Namespace="AWS/Bedrock",
            MetricName="GuardrailInterventions",
            Dimensions=[{'Name': 'GuardrailId', 'Value': guardrail_id}, {'Name': 'FilterType', 'Value': 'PROMPT_ATTACK'}],
            Period=300,
            EvaluationPeriods=1,
            Threshold=5.0,
            ComparisonOperator='GreaterThanThreshold',
            Statistic='Sum',
            AlarmActions=[sns_topic_arn]
        )
        return {'status': 'ALARM_PROVISIONED', 'alarm_name': alarm_name}

if __name__ == '__main__':
    alerting = BedrockGuardrailAlertingEngine()
    print("BedrockGuardrailAlertingEngine initialized and configured.")

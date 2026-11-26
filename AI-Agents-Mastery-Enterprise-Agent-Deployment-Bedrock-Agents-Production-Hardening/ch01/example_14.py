class BedrockMetricAlarmManager:
    """Deploys CloudWatch Metric Filters to alert on Bedrock Action Group failure spikes."""

    @staticmethod
    def generate_metric_filter_definition(log_group: str) -> dict:
        return {
            "filterName": "BedrockActionGroupFailureRate",
            "filterPattern": '[time, event_id, status_code >= 400, msg]',
            "metricTransformations": [
                {
                    "metricName": "ActionGroupFailures",
                    "metricNamespace": "AWS/BedrockAgents",
                    "metricValue": "1"
                }
            ]
        }

if __name__ == "__main__":
    filt = BedrockMetricAlarmManager.generate_metric_filter_definition("/aws/bedrock/agents/sre-agent")
    print("-> CloudWatch Metric Filter Definition Ready:")
    print(f"   Metric: {filt['metricTransformations'][0]['metricName']}")

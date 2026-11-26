from typing import Dict, Any

class BedrockPromptOverrideManager:
    """Manages custom prompt templates for Bedrock orchestration loops."""

    @staticmethod
    def get_strict_sre_orchestration_template() -> str:
        return """
You are an Enterprise Autonomous SRE Agent.
You have access to the following Action Groups:
$action_groups$

When diagnosing outages, follow this strict verification checklist:
1. Formulate a precise hypothesis before issuing any tool query.
2. Check recent CloudWatch alarms and deployment markers.
3. Validate tool outputs against known schema boundaries.
4. If an external service returns 5xx, execute exponential backoff.
Never recommend destructive actions without explicit operator sign-off.
"""

if __name__ == "__main__":
    template = BedrockPromptOverrideManager.get_strict_sre_orchestration_template()
    print("-> Custom SRE Orchestration Prompt Template Loaded:")
    print(f"   Length: {len(template)} characters")

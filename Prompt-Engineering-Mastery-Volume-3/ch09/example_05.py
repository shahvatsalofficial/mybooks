"""
Tool Failure Triage Middleware: Intercepts raw system exceptions, categorizes them
into standardized taxonomies, and injects structured diagnostic XML into agent context.
"""

from typing import Dict, Any, Tuple, Optional
import traceback
import json


class ToolFailureTriageMiddleware:
    """Translates raw infrastructure errors into structured agent recovery prompts."""

    @staticmethod
    def triage_exception(tool_name: str, raw_exception: Exception) -> Dict[str, Any]:
        """Categorizes exception into standardized enterprise failure classes."""
        exc_str = str(raw_exception).lower()
        exc_type = type(raw_exception).__name__

        # 1. Check for Rate Limiting / Throttling
        if "429" in exc_str or "too many requests" in exc_str or "rate limit" in exc_str:
            return {
                "category": "TRANSIENT_RATE_LIMITED",
                "recovery_strategy": "EXPONENTIAL_BACKOFF",
                "recommended_retry": True,
                "diagnostic": "Downstream service throttled request. Backoff required."
            }

        # 2. Check for Schema / Formatting Error
        if "validation" in exc_str or "jsondecode" in exc_str or "invalid format" in exc_str:
            return {
                "category": "SCHEMA_VALIDATION_ERROR",
                "recovery_strategy": "PARAMETER_CORRECTION",
                "recommended_retry": False,
                "diagnostic": f"Parameter validation failed: {str(raw_exception)}. Re-serialize arguments."
            }

        # 3. Check for Permissions / Security Boundary
        if "401" in exc_str or "403" in exc_str or "access denied" in exc_str or "unauthorized" in exc_str:
            return {
                "category": "HARD_PERMISSION_DENIED",
                "recovery_strategy": "HUMAN_ESCALATION",
                "recommended_retry": False,
                "diagnostic": "IAM role or OAuth token lacks required scope. Do not retry."
            }

        # 4. Check for Server Outage / Timeout
        if "timeout" in exc_str or "502" in exc_str or "503" in exc_str or "504" in exc_str:
            return {
                "category": "TRANSIENT_OUTAGE",
                "recovery_strategy": "FALLBACK_OR_RETRY",
                "recommended_retry": True,
                "diagnostic": "Upstream service timeout or outage. Retry once or drop to fallback tier."
            }

        # Default Unhandled Fault
        return {
            "category": "UNKNOWN_SYSTEM_FAULT",
            "recovery_strategy": "EVALUATE_OR_ABORT",
            "recommended_retry": False,
            "diagnostic": f"Unhandled error [{exc_type}]: {str(raw_exception)}"
        }

    def format_failure_observation(self, tool_name: str, raw_exception: Exception) -> str:
        """Emits structured XML observation for LLM consumption."""
        triage = self.triage_exception(tool_name, raw_exception)
        return f"""<observation status="TOOL_EXECUTION_FAILURE">
  <tool_name>{tool_name}</tool_name>
  <failure_category>{triage["category"]}</failure_category>
  <recommended_strategy>{triage["recovery_strategy"]}</recommended_strategy>
  <diagnostic_detail>{triage["diagnostic"]}</diagnostic_detail>
  <allow_retry>{str(triage["recommended_retry"]).lower()}</allow_retry>
</observation>"""

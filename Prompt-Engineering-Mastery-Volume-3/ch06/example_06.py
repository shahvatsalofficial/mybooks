"""
Hallucination Quarantine Middleware: Intercepts tool execution payloads,
running them through pre-flight factuality verification before dispatching to physical infrastructure.
"""

from typing import Dict, Any, Callable


class HallucinationQuarantineMiddleware:
    """Wraps agent tool execution in an automated verification firewall."""

    def __init__(self, factuality_verifier: DualPassFactualityVerifier, audit_sink: Any):
        self.verifier = factuality_verifier
        self.audit_sink = audit_sink

    def intercept_and_execute(
        self,
        tool_name: str,
        tool_params: Dict[str, Any],
        supporting_prose: str,
        reference_documents: List[Dict[str, str]],
        physical_executor: Callable[[Dict[str, Any]], Any]
    ) -> Dict[str, Any]:
        """
        Intercepts tool call, evaluates grounding of supporting prose and arguments.
        Dispatches if valid; quarantines if ungrounded.
        """
        is_grounded, score, telemetry = self.verifier.audit_draft_output(
            supporting_prose, reference_documents
        )

        self.audit_sink.record_event({
            "tool_name": tool_name,
            "faithfulness_score": score,
            "telemetry": telemetry,
            "grounded": is_grounded
        })

        if not is_grounded:
            return {
                "status": "QUARANTINED",
                "error": "EXECUTION_BLOCKED_BY_FIREWALL",
                "reason": f"Faithfulness score ({score:.2f}) below required threshold (0.95).",
                "failed_claims": [t for t in telemetry if t["status"] == "UNGROUNDED"]
            }

        return physical_executor(tool_params)

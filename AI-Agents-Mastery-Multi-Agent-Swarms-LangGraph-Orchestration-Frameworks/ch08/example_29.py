import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class ExecutionSpan(BaseModel):
    span_id: str
    parent_span_id: Optional[str] = None
    agent_name: str
    status: str # SUCCESS, TIMEOUT, ERROR
    duration_ms: float
    error_details: Optional[str] = None
    input_payload: Dict[str, Any] = Field(default_factory=dict)

class IncidentRunbookGenerator:
    """Parses distributed trace spans and generates structured SRE remediation runbooks."""
    
    @classmethod
    def analyze_trace_and_generate_runbook(cls, incident_id: str, spans: List[ExecutionSpan]) -> str:
        failed_spans = [s for s in spans if s.status != "SUCCESS"]
        if not failed_spans:
            return "No anomalies detected in execution trace."
            
        root_culprit = failed_spans[0]
        total_time_ms = sum(s.duration_ms for s in spans)
        
        runbook = (
            f"# SRE Incident Remediation Runbook: {incident_id}\n\n"
            f"**Severity**: P1 - HIGH CONCURRENCY OUTAGE\n"
            f"**Root Failure Node**: `{root_culprit.agent_name}` (Span: `{root_culprit.span_id}`)\n"
            f"**Failure Mode**: `{root_culprit.status}` - {root_culprit.error_details}\n"
            f"**Total Trace Latency**: {total_time_ms:.1f}ms across {len(spans)} spans\n\n"
            f"### Immediate Containment Steps:\n"
            f"1. **Isolate Agent Node**: Trip circuit breaker on `{root_culprit.agent_name}` to fallback to heuristic baseline.\n"
            f"2. **Purge Checkpointer Write-Ahead Log**: Clear poisoned lock key on session thread.\n"
            f"3. **Inspect Problematic Input Payload**:\n"
            f"   ```json\n"
            f"   {root_culprit.input_payload}\n"
            f"   ```\n"
            f"4. **Restart Kubernetes Replica**: `kubectl rollout restart deployment/agent-{root_culprit.agent_name.lower()}`\n"
        )
        print(f"[RUNBOOK GENERATOR] Successfully generated emergency runbook for incident '{incident_id}'.")
        return runbook

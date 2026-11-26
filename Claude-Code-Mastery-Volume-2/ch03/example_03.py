@mcp.prompt()
def triage_production_incident(incident_id: str, severity: str = "P1") -> str:
    """Synthesizes a high-priority incident triage prompt for SRE responders.
    
    Args:
        incident_id: Active PagerDuty or Opsgenie alert identifier.
        severity: Incident severity classification (P1, P2, P3).
    """
    return f"""You are the Lead SRE Incident Commander responding to an active {severity} production outage.
Incident ID: {incident_id}

Execute the following deterministic triage procedure:
1. Use the 'query_cluster_metrics' tool to inspect error rates across microservices over the past 30 minutes.
2. Read the resource 'incident://{incident_id}/logs' to extract fatal stack traces.
3. Formulate an immediate hypothesis regarding root cause (network partition, database lock, bad canary).
4. Propose an isolated mitigation step before taking destructive action.
"""

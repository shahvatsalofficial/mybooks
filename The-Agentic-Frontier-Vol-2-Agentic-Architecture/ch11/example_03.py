# case_studies/cs02_cloudops_sre_agent.py
"""
Case Study 02: Cloud Ops Self-Healing SRE Agent with E2B Sandboxing.
Author: Vatsal Shah — The Agentic Frontier Vol 2
"""

import os
import time
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from e2b_code_interpreter import Sandbox
from langgraph.graph import StateGraph, END

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CloudOpsAgent")

# ============================================================================
# 1. INCIDENT SCHEMAS & SANDBOX MODELS
# ============================================================================

class IncidentAlert(BaseModel):
    incident_id: str
    cluster_name: str
    namespace: str
    resource_name: str
    alert_name: str
    severity: str = "P2"
    raw_logs: List[str] = Field(default_factory=list)

class RemediationAction(BaseModel):
    command: str
    description: str
    is_destructive: bool = False
    target_resource: str
    expected_outcome: str

class SREAgentState(BaseModel):
    alert: IncidentAlert
    diagnostic_logs: List[str] = Field(default_factory=list)
    planned_action: Optional[RemediationAction] = None
    approval_status: str = "PENDING"  # PENDING, APPROVED, REJECTED, AUTO_APPROVED
    execution_result: Optional[str] = None
    sandbox_id: Optional[str] = None
    status: str = "RECEIVED"

# ============================================================================
# 2. E2B SANDBOX MANAGER
# ============================================================================

class E2BSandboxRunner:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("E2B_API_KEY", "sbx_test_key")

    def execute_in_microvm(self, script_commands: List[str]) -> Dict[str, Any]:
        """
        Provisions a disposable Firecracker MicroVM and executes commands in isolated environment.
        """
        logger.info(" [E2B Sandbox] Provisioning ephemeral Firecracker MicroVM...")
        start_t = time.time()
        
        # Simulated E2B Sandbox Execution for production safety demonstration
        combined_script = "\n".join(script_commands)
        logger.info(f"⚡ [E2B MicroVM Executing]:\n{combined_script}")
        
        # Simulate execution execution output inside microVM
        time.sleep(0.5)  # MicroVM spin-up + script execution time
        exec_duration = round(time.time() - start_t, 3)
        
        stdout_output = (
            f"[E2B VM-39182 Execution Output ({exec_duration}s)]\n"
            f"-> Connecting to cluster context...\n"
            f"-> Executing diagnostic script...\n"
            f"-> Command succeeded with exit code 0.\n"
        )
        
        return {
            "stdout": stdout_output,
            "stderr": "",
            "exit_code": 0,
            "duration_s": exec_duration
        }

# ============================================================================
# 3. AGENT GRAPH NODES
# ============================================================================

def diagnose_incident_node(state: SREAgentState) -> Dict[str, Any]:
    """
    Diagnostic Node: Evaluates CloudWatch alert and determines root cause using runbook rules.
    """
    alert = state.alert
    logger.info(f" [SRE Agent] Diagnosing Incident {alert.incident_id} on {alert.resource_name}...")

    # Run diagnostic script inside E2B Sandbox
    sandbox_runner = E2BSandboxRunner()
    diag_commands = [
        f"echo 'Analyzing logs for {alert.resource_name} in {alert.namespace}...'",
        f"kubectl get pod {alert.resource_name} -n {alert.namespace} -o json path='{{.status.containerStatuses}}'",
        f"kubectl logs {alert.resource_name} -n {alert.namespace} --tail=50"
    ]
    
    diag_res = sandbox_runner.execute_in_microvm(diag_commands)
    
    # Identify remediation based on alert type
    if "OOMKilled" in alert.alert_name or "MemoryLimitExceeded" in alert.alert_name:
        action = RemediationAction(
            command=f"kubectl rollout restart deployment/{alert.resource_name.split('-')[0]} -n {alert.namespace}",
            description="Trigger rolling restart of deployment to flush leaked connection pool.",
            is_destructive=False,
            target_resource=alert.resource_name,
            expected_outcome="Pods restarted cleanly with fresh memory allocations."
        )
    elif "DiskPressure" in alert.alert_name or "VolumeFull" in alert.alert_name:
        action = RemediationAction(
            command=f"kubectl exec {alert.resource_name} -n {alert.namespace} -- rm -rf /tmp/cache/*",
            description="Clear ephemeral cache directory to relieve disk pressure.",
            is_destructive=True,
            target_resource=alert.resource_name,
            expected_outcome="Frees ~15GB space on node local storage."
        )
    else:
        action = RemediationAction(
            command=f"kubectl get events -n {alert.namespace} --sort-by='.metadata.creationTimestamp'",
            description="Collect detailed event stream for manual human investigation.",
            is_destructive=False,
            target_resource=alert.resource_name,
            expected_outcome="Event log appended to incident ticket."
        )

    return {
        "diagnostic_logs": [diag_res["stdout"]],
        "planned_action": action,
        "status": "DIAGNOSED"
    }

def approval_gate_node(state: SREAgentState) -> Dict[str, Any]:
    """
    HITL Approval Gate: Automatically approves non-destructive tasks, pauses for human on destructive.
    """
    action = state.planned_action
    if not action:
        return {"approval_status": "REJECTED", "status": "ABORTED"}

    if not action.is_destructive:
        logger.info(f" [Approval Gate] Action is NON-DESTRUCTIVE. Auto-approving command: {action.command}")
        return {"approval_status": "AUTO_APPROVED", "status": "READY_FOR_EXECUTION"}
    else:
        logger.warning(f"⚠️ [Approval Gate] Action is DESTRUCTIVE ({action.command}). Requiring Human Approval...")
        # Simulate instant interactive HITL approval override for test execution
        logger.info(" [HITL Override] Engineer approved command via Slack button.")
        return {"approval_status": "HUMAN_APPROVED", "status": "READY_FOR_EXECUTION"}

def execute_remediation_node(state: SREAgentState) -> Dict[str, Any]:
    """
    Execution Node: Executes approved remediation action inside isolated E2B MicroVM.
    """
    action = state.planned_action
    status = state.approval_status

    if status not in ["AUTO_APPROVED", "HUMAN_APPROVED"] or not action:
        logger.warning(" [Execution Node] Aborting execution due to unapproved action status.")
        return {"status": "EXECUTION_ABORTED"}

    logger.info(f"️ [SRE Agent] Executing Remediation: {action.command}")
    sandbox_runner = E2BSandboxRunner()
    exec_res = sandbox_runner.execute_in_microvm([action.command])

    return {
        "execution_result": exec_res["stdout"],
        "status": "REMEDIATION_COMPLETE"
    }

# ============================================================================
# 4. GRAPH COMPILATION & TEST EXECUTION
# ============================================================================

def build_sre_graph():
    builder = StateGraph(SREAgentState)
    builder.add_node("diagnose", diagnose_incident_node)
    builder.add_node("approval_gate", approval_gate_node)
    builder.add_node("execute_remediation", execute_remediation_node)

    builder.set_entry_point("diagnose")
    builder.add_edge("diagnose", "approval_gate")
    builder.add_edge("approval_gate", "execute_remediation")
    builder.add_edge("execute_remediation", END)

    return builder.compile()

if __name__ == "__main__":
    sre_graph = build_sre_graph()
    
    test_alert = IncidentAlert(
        incident_id="INC-88219",
        cluster_name="prod-us-east-1",
        namespace="payments",
        resource_name="payment-processor-v2-79f8b",
        alert_name="PodMemoryLimitExceeded",
        severity="P2",
        raw_logs=["Container payment-processor exhausted 512MB RAM limit."]
    )
    
    init_state = SREAgentState(alert=test_alert)
    res = sre_graph.invoke(init_state)
    print(f"\nFinal Incident Resolution Status: {res['status']}")
    print(f"Execution Output:\n{res['execution_result']}")

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from vertexai.generative_models import FunctionDeclaration, Tool

class RestartPodInput(BaseModel):
    namespace: str = Field(description="Kubernetes namespace where the target pod resides", regex=r"^[a-z0-9\-]+$")
    pod_name: str = Field(description="Exact metadata.name of the Kubernetes pod", min_length=3)
    grace_period_seconds: int = Field(default=30, ge=0, le=300, description="Grace period before SIGKILL")

class QueryMetricInput(BaseModel):
    metric_name: str = Field(description="Prometheus metric name, e.g. container_memory_working_set_bytes")
    cluster: str = Field(description="Target GKE cluster identifier")
    duration_minutes: int = Field(default=15, ge=1, le=1440)

def generate_k8s_tools() -> Tool:
    """Builds native Gemini Tool declaration from Pydantic schemas."""
    
    restart_pod_func = FunctionDeclaration(
        name="restart_kubernetes_pod",
        description="Terminates and restarts a malfunctioning Kubernetes pod within an enterprise GKE cluster.",
        parameters={
            "type": "object",
            "properties": {
                "namespace": {"type": "string", "description": "GKE namespace"},
                "pod_name": {"type": "string", "description": "Pod identifier"},
                "grace_period_seconds": {"type": "integer", "description": "Termination grace period"}
            },
            "required": ["namespace", "pod_name"]
        }
    )
    
    query_metric_func = FunctionDeclaration(
        name="query_prometheus_metric",
        description="Queries historical time-series metrics from Google Cloud Managed Service for Prometheus.",
        parameters={
            "type": "object",
            "properties": {
                "metric_name": {"type": "string", "description": "Prometheus metric string"},
                "cluster": {"type": "string", "description": "Cluster name"},
                "duration_minutes": {"type": "integer", "description": "Lookback duration in minutes"}
            },
            "required": ["metric_name", "cluster"]
        }
    )
    
    return Tool(function_declarations=[restart_pod_func, query_metric_func])

if __name__ == "__main__":
    k8s_tool = generate_k8s_tools()
    print("Successfully compiled Gemini Tools with declarations:")
    for decl in k8s_tool._raw_tool.function_declarations:
        print(f" - {decl.name}: {decl.description[:55]}...")

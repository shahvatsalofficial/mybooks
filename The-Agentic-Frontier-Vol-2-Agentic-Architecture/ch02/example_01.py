from pydantic import BaseModel, Field
from typing import Literal

class RestartContainerInput(BaseModel):
    """Schema for restarting a target Kubernetes microservice container pod."""
    cluster_id: Literal["prod-us-east-1", "prod-eu-west-1", "staging-us-central"] = Field(
        ..., description="Target Kubernetes cluster identifier."
    )
    namespace: str = Field(
        ..., min_length=2, max_length=63, description="Kubernetes namespace (e.g., 'trading-engine')."
    )
    pod_name: str = Field(
        ..., description="Exact pod name to restart."
    )
    grace_period_seconds: int = Field(
        default=30, ge=0, le=300, description="Graceful termination period in seconds."
    )

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal, Optional
import re

class KubernetesScaleInput(BaseModel):
    namespace: str = Field(
        default="production",
        description="Kubernetes namespace (e.g. 'production', 'kube-system')"
    )
    deployment_name: str = Field(
        ...,
        min_length=1,
        max_length=63,
        description="Target Deployment or StatefulSet resource identifier"
    )
    replicas: int = Field(
        ...,
        ge=0,
        le=50,
        description="Desired target replica count (bounded between 0 and 50)"
    )
    reason: str = Field(
        ...,
        min_length=10,
        max_length=256,
        description="Mandatory audit trail rationale explaining why scaling is required"
    )

    @field_validator("deployment_name")
    @classmethod
    def validate_k8s_dns_name(cls, v: str) -> str:
        pattern = r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$"
        if not re.match(pattern, v):
            raise ValueError(f"'{v}' is not a valid RFC 1123 Kubernetes deployment name")
        return v

from enum import Enum
from pydantic import BaseModel, Field

class DeploymentEnvironment(str, Enum):
    DEVELOPMENT = "dev"
    STAGING = "staging"
    PRODUCTION = "prod"

class ResourceLimits(BaseModel):
    cpu_cores: float = Field(1.0, ge=0.1, le=64.0)
    memory_gb: int = Field(2, ge=1, le=256)

class AdvancedDeployRequest(BaseModel):
    service: str = Field(..., min_length=2)
    env: DeploymentEnvironment = Field(DeploymentEnvironment.STAGING)
    limits: ResourceLimits = Field(default_factory=ResourceLimits)

@mcp.tool()
def deploy_advanced(request: AdvancedDeployRequest) -> str:
    """Executes a deployment with nested resource limits and environment enums."""
    return f"Deploying {request.service} to {request.env.value} with {request.limits.cpu_cores} CPUs."

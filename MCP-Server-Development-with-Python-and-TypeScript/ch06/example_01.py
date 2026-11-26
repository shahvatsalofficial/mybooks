from mcp.server.fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP("SchemaDemoServer")

@mcp.tool()
def deploy_microservice(
    service_name: str = Field(
        ...,
        pattern="^[a-z0-9-]+$",
        description="Kubernetes lowercase service identifier."
    ),
    replica_count: int = Field(
        3,
        ge=1,
        le=50,
        description="Target pod replica count between 1 and 50."
    ),
    enable_canary: bool = Field(
        False,
        description="Whether to route 10% traffic to canary deployment."
    )
) -> str:
    """Deploys a containerized microservice to the active Kubernetes cluster."""
    return f"Deployment initiated for {service_name} with {replica_count} replicas."

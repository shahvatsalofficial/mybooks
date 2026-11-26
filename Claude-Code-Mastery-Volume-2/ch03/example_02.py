from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum

mcp = FastMCP("DataOps-Platform")

class AggregationType(str, Enum):
    SUM = "SUM"
    AVG = "AVG"
    MEDIAN = "MEDIAN"
    P99 = "P99"

class MetricFilter(BaseModel):
    environment: Literal["production", "staging", "development"] = Field(
        default="production",
        description="Target deployment tier to filter metrics"
    )
    service_name: str = Field(
        ...,
        min_length=3,
        max_length=64,
        description="Exact microservice name registered in Consul service registry"
    )
    aggregation: AggregationType = Field(
        default=AggregationType.AVG,
        description="Statistical reduction algorithm to apply across the sample window"
    )
    time_window_minutes: int = Field(
        default=60,
        ge=5,
        le=1440,
        description="Sliding historical time window in minutes (5m to 24h)"
    )

@mcp.tool()
async def query_cluster_metrics(filter_params: MetricFilter) -> str:
    """Queries cluster operational metrics from enterprise VictoriaMetrics/Prometheus.
    
    Args:
        filter_params: Validated metric aggregation and filtering criteria.
    """
    # filter_params is guaranteed to be a fully validated Pydantic model instance!
    return f"Aggregated {filter_params.aggregation.value} metrics for {filter_params.service_name} over {filter_params.time_window_minutes}m."

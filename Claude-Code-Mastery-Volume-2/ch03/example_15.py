#!/usr/bin/env python3
"""
Enterprise Polars & Apache Arrow Analytical Engine
Language: Python 3.11+
Executes zero-copy vectorized columnar analytics over massive Parquet datasets
"""

from mcp.server.fastmcp import FastMCP, Context
from pydantic import BaseModel, Field
import polars as pl
import asyncio

mcp = FastMCP("Enterprise-Polars-Engine")

class PolarsAggregationInput(BaseModel):
    parquet_path: str = Field(..., description="Path to Parquet file on local or S3 filesystem")
    group_by_column: str = Field(..., description="Categorical column to group records by")
    metric_column: str = Field(..., description="Numeric column to aggregate")
    operation: str = Field(default="sum", description="Reduction operation: sum, mean, min, max, median")

@mcp.tool()
async def compute_polars_aggregation(input_data: PolarsAggregationInput, ctx: Context) -> str:
    """Executes multi-threaded SIMD columnar aggregation using the Polars lazy execution engine."""
    ctx.info(f"Scanning Parquet dataset: {input_data.parquet_path} via Polars LazyFrame...")
    
    def _execute_lazy_polars():
        # Lazy scan avoids reading entire file into RAM!
        lf = pl.scan_parquet(input_data.parquet_path)
        
        agg_expr = getattr(pl.col(input_data.metric_column), input_data.operation)()
        result = (
            lf.group_by(input_data.group_by_column)
            .agg(agg_expr.alias(f"{input_data.metric_column}_{input_data.operation}"))
            .sort(f"{input_data.metric_column}_{input_data.operation}", descending=True)
            .limit(25)
            .collect() # Executes in parallel Rust worker threads!
        )
        return result.to_pandas().to_markdown(index=False)
        
    try:
        # Offload Rust computation to thread pool to preserve event loop responsiveness
        markdown_output = await asyncio.to_thread(_execute_lazy_polars)
        return f"### Polars Columnar Summary ({input_data.operation.upper()} on {input_data.metric_column}):\n\n" + markdown_output
    except Exception as err:
        return f"POLARS EXECUTION FAILED: {str(err)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")

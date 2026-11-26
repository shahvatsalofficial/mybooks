"""
recipe_4_2_fastmcp_cancellable_tool.py
Production Python FastMCP tool featuring Pydantic V2 validation and cancellation token listening.
"""

import asyncio
import sys
from typing import List
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("CancellableComputeServer")


class BatchProcessingRequest(BaseModel):
    record_ids: List[int] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Array of integer database record IDs to re-index."
    )
    batch_label: str = Field(
        ...,
        pattern=r"^[A-Z0-9_-]+$",
        description="Uppercase alphanumeric batch identifier."
    )
    delay_per_item_ms: int = Field(
        default=50,
        ge=0,
        le=1000,
        description="Simulated processing latency per item."
    )


@mcp.tool(
    name="batch_reindex_records",
    description="Asynchronously re-index database records with cooperative cancellation monitoring."
)
async def batch_reindex_records(
    params: BatchProcessingRequest,
    ctx: Context
) -> str:
    """Executes batch processing, actively listening for client-side cancellation."""
    total = len(params.record_ids)
    processed = 0

    sys.stderr.write(f"[Batch] Starting batch '{params.batch_label}' with {total} records...\n")

    for idx, record_id in enumerate(params.record_ids, start=1):
        # 1. Cooperative Cancellation Check
        # If client issued notifications/cancelled, terminate cleanly
        if ctx.session and ctx.session.is_cancelled():
            sys.stderr.write(f"[Batch] Cancellation signal received at record {record_id}!\n")
            return f"OperationCancelled: Processed {processed}/{total} records before aborting."

        # 2. Simulate compute work
        await asyncio.sleep(params.delay_per_item_ms / 1000.0)
        processed += 1

        # 3. Emit real-time progress update to client host
        if idx % 10 == 0 or idx == total:
            await ctx.report_progress(progress=idx, total=total)

    return f"Success: Completed batch '{params.batch_label}'. Processed {processed} records."


if __name__ == "__main__":
    mcp.run(transport="stdio")

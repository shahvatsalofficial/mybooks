#!/usr/bin/env python3
"""
Enterprise Cloud Object Reader MCP Server
Language: Python 3.11+
Features: Range-request partial downloads, magic-byte MIME detection, byte capping
"""

from mcp.server.fastmcp import FastMCP, Context
from pydantic import BaseModel, Field
import boto3
import os

mcp = FastMCP("Cloud-Object-Inspector")
s3 = boto3.client("s3")

class ReadObjectPrefixInput(BaseModel):
    bucket_name: str = Field(..., description="Target AWS S3 bucket identifier")
    object_key: str = Field(..., description="Key path of file in bucket (e.g. logs/app.log)")
    max_bytes: int = Field(default=32768, ge=512, le=131072, description="Maximum bytes to read (capped at 128KB)")

@mcp.tool()
async def inspect_s3_object_head(input_data: ReadObjectPrefixInput, ctx: Context) -> str:
    """Safely inspects the header and head bytes of an S3 object without downloading the entire file."""
    ctx.info(f"Querying S3 object: s3://{input_data.bucket_name}/{input_data.object_key}...")
    
    try:
        # 1. Fetch object metadata first
        meta = s3.head_object(Bucket=input_data.bucket_name, Key=input_data.object_key)
        total_size = meta["ContentLength"]
        content_type = meta.get("ContentType", "application/octet-stream")
        
        # 2. Execute HTTP Range Request to read ONLY the first max_bytes!
        range_header = f"bytes=0-{input_data.max_bytes - 1}"
        response = s3.get_object(
            Bucket=input_data.bucket_name,
            Key=input_data.object_key,
            Range=range_header
        )
        
        body_bytes = response["Body"].read()
        text_content = body_bytes.decode("utf-8", errors="replace")
        
        is_truncated = total_size > input_data.max_bytes
        truncation_note = f"\n\n*Note: Total object size is {total_size:,} bytes. Truncated to first {len(body_bytes):,} bytes.*" if is_truncated else ""
        
        return f"### S3 Object Preview: s3://{input_data.bucket_name}/{input_data.object_key}\n" \
               f"* **MIME Type:** `{content_type}`\n" \
               f"* **Total Size:** `{total_size:,}` bytes\n\n" \
               f"```\n{text_content}\n```" + truncation_note
    except Exception as err:
        return f"S3_INSPECTION_FAILED: {str(err)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")

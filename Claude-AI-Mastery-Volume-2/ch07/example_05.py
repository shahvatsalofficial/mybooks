"""
Recipe 07.5: Enterprise AWS S3 Object Storage MCP Connector
Author: Vatsal Shah (Vatsal Shah)
License: Apache-2.0
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("S3Connector")

mcp = FastMCP("enterprise-s3-connector")
s3_client = boto3.client("s3", region_name=os.getenv("AWS_REGION", "us-east-1"))

MAX_FILE_BYTES = 5 * 1024 * 1024  # 5MB maximum inline ingestion ceiling
ALLOWED_EXTENSIONS = {".txt", ".md", ".json", ".csv", ".log", ".yaml", ".yml"}

@mcp.tool()
def read_s3_text_object(bucket: str, key: str) -> str:
    """Reads the text content of an S3 object within strict 5MB size limits."""
    # Verify file extension
    _, ext = os.path.splitext(key.lower())
    if ext not in ALLOWED_EXTENSIONS:
        return json.dumps({
            "status": "REJECTED",
            "error": f"File extension '{ext}' is prohibited. Only text/data formats allowed."
        })

    try:
        # Check object metadata first (head_object) to prevent downloading massive binaries
        head = s3_client.head_object(Bucket=bucket, Key=key)
        content_length = head.get("ContentLength", 0)

        if content_length > MAX_FILE_BYTES:
            return json.dumps({
                "status": "OVERSIZED",
                "error": f"Object size ({content_length} bytes) exceeds 5MB ceiling. Use generate_presigned_download_url instead.",
                "size_bytes": content_length
            })

        response = s3_client.get_object(Bucket=bucket, Key=key)
        text_content = response["Body"].read().decode("utf-8", errors="replace")
        return json.dumps({
            "status": "SUCCESS",
            "bucket": bucket,
            "key": key,
            "size_bytes": content_length,
            "content": text_content
        })

    except ClientError as e:
        logger.error(f"S3 ClientError for s3://{bucket}/{key}: {e}")
        return json.dumps({"status": "ERROR", "error": str(e)})

@mcp.tool()
def generate_presigned_download_url(bucket: str, key: str, expires_in_seconds: int = 900) -> str:
    """Generates a secure, temporary pre-signed URL for direct browser downloading of large files."""
    try:
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=min(expires_in_seconds, 3600)
        )
        return json.dumps({"bucket": bucket, "key": key, "presigned_url": url, "expires_in_seconds": expires_in_seconds})
    except ClientError as e:
        return json.dumps({"status": "ERROR", "error": str(e)})

if __name__ == "__main__":
    mcp.run()

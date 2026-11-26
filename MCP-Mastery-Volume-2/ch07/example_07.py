"""
presigned_storage_bridge.py - Ephemeral Cloud Storage URL Generator
Generates cryptographically signed URLs for AWS S3 and Google Cloud Storage.
"""

import os
import logging
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger("PresignedStorageBridge")


class PresignedStorageManager:
    """Issues temporary, policy-bounded presigned URLs for S3 and GCS."""

    def __init__(self, allowed_buckets: Optional[set] = None, default_ttl_seconds: int = 900):
        self.allowed_buckets = allowed_buckets or set(
            os.environ.get("ALLOWED_STORAGE_BUCKETS", "data-lake-prod,model-weights").split(",")
        )
        self.default_ttl = default_ttl_seconds
        self.s3_client = boto3.client("s3")

    def generate_s3_url(
        self,
        bucket: str,
        key: str,
        operation: str = "read",
        ttl_seconds: Optional[int] = None,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generates a SigV4 presigned URL for S3 GetObject or PutObject."""
        if bucket not in self.allowed_buckets:
            raise PermissionError(f"Security Alert: Bucket '{bucket}' is not in authorized registry.")

        ttl = ttl_seconds or self.default_ttl
        # Enforce maximum 1-hour expiration ceiling
        ttl = min(ttl, 3600)

        client_method = "get_object" if operation == "read" else "put_object"
        method_params = {"Bucket": bucket, "Key": key}

        if operation == "write" and content_type:
            method_params["ContentType"] = content_type

        try:
            logger.info(f"Generating presigned {operation.upper()} URL for s3://{bucket}/{key} (TTL={ttl}s)")
            url = self.s3_client.generate_presigned_url(
                ClientMethod=client_method,
                Params=method_params,
                ExpiresIn=ttl
            )
            return {
                "status": "success",
                "uri": f"storage://s3/{bucket}/{key}",
                "url": url,
                "operation": operation,
                "expires_in_seconds": ttl,
                "http_method": "GET" if operation == "read" else "PUT",
                "required_headers": {"Content-Type": content_type} if content_type else {}
            }
        except ClientError as e:
            logger.error(f"Failed to generate presigned S3 URL: {e}")
            raise RuntimeError(f"Cloud Cryptographic Signing Failed: {e}")


# FastMCP Tool Binding
from mcp.server.fastmcp import FastMCP
storage_tool_mcp = FastMCP("Presigned-URL-Provider")
manager = PresignedStorageManager()


@storage_tool_mcp.tool()
async def get_presigned_url(
    storage_uri: str,
    operation: str = "read",
    ttl_seconds: int = 900,
    content_type: Optional[str] = None
) -> Dict[str, Any]:
    """Generates an ephemeral, cryptographically signed URL to bypass memory buffers.
    
    Args:
        storage_uri: URI formatted as 'storage://s3/{bucket}/{key}'
        operation: 'read' for GET download, 'write' for PUT upload.
        ttl_seconds: Lifespan of the signed link in seconds (max 3600).
        content_type: Required MIME type when operation is 'write'.
    """
    if not storage_uri.startswith("storage://s3/"):
        raise ValueError("Currently, presigned URLs are supported for 'storage://s3/' URIs.")
        
    parts = storage_uri.replace("storage://s3/", "").split("/", 1)
    if len(parts) != 2:
        raise ValueError("Malformed S3 URI. Expected 'storage://s3/{bucket}/{key}'.")
        
    bucket, key = parts[0], parts[1]
    return manager.generate_s3_url(bucket, key, operation, ttl_seconds, content_type)

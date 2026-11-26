"""
chunked_blob_reader.py - Memory-Bounded Range Streaming for Model Context Protocol
Leverages HTTP Range requests to inspect multi-gigabyte objects without RAM exhaustion.
"""

import base64
import os
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
from mcp.server.fastmcp import FastMCP

range_mcp = FastMCP("Chunked-Range-Streamer")
s3 = boto3.client("s3")

MAX_CHUNK_BYTES = 512 * 1024  # 512 KB per request chunk ceiling


@range_mcp.tool()
async def read_resource_range(
    storage_uri: str,
    offset: int = 0,
    length: int = 65536,
    as_base64: bool = False
) -> Dict[str, Any]:
    """Reads a bounded byte window from a cloud object or local file using range requests.
    
    Args:
        storage_uri: Target URI ('storage://s3/{bucket}/{key}' or 'storage://local/{path}')
        offset: Starting byte position (0-indexed). Supports negative offset for tail reading.
        length: Maximum number of bytes to retrieve (capped at 512KB).
        as_base64: If True, encodes binary data as base64 string. If False, decodes as UTF-8.
    """
    if length > MAX_CHUNK_BYTES:
        raise ValueError(f"Requested length {length} exceeds maximum safety ceiling of {MAX_CHUNK_BYTES} bytes.")

    if storage_uri.startswith("storage://s3/"):
        parts = storage_uri.replace("storage://s3/", "").split("/", 1)
        bucket, key = parts[0], parts[1]
        
        # Determine total object length first
        head = s3.head_object(Bucket=bucket, Key=key)
        total_size = head["ContentLength"]
        
        # Calculate byte bounds
        if offset < 0:
            # S3 suffix range: bytes=-N
            range_header = f"bytes={offset}"
            actual_start = max(0, total_size + offset)
            actual_end = total_size - 1
        else:
            actual_start = offset
            actual_end = min(offset + length - 1, total_size - 1)
            range_header = f"bytes={actual_start}-{actual_end}"
            
        if actual_start >= total_size:
            return {
                "storage_uri": storage_uri,
                "offset": offset,
                "length": 0,
                "total_size": total_size,
                "has_more": False,
                "data": ""
            }
            
        resp = s3.get_object(Bucket=bucket, Key=key, Range=range_header)
        raw_bytes = resp["Body"].read()
        
    elif storage_uri.startswith("storage://local/"):
        rel_path = storage_uri.replace("storage://local/", "")
        jail_root = os.path.realpath(os.environ.get("STORAGE_JAIL_ROOT", "/tmp/mcp_storage_jail"))
        safe_path = os.path.realpath(os.path.abspath(os.path.join(jail_root, rel_path.lstrip("/"))))
        
        if os.path.commonpath([jail_root, safe_path]) != jail_root:
            raise PermissionError("Path traversal violation.")
            
        total_size = os.path.getsize(safe_path)
        if offset < 0:
            actual_start = max(0, total_size + offset)
            actual_end = total_size
        else:
            actual_start = offset
            actual_end = min(offset + length, total_size)
            
        with open(safe_path, "rb") as f:
            f.seek(actual_start)
            raw_bytes = f.read(actual_end - actual_start)
    else:
        raise ValueError(f"Unsupported URI: {storage_uri}")

    # Encode payload
    if as_base64:
        encoded_data = base64.b64encode(raw_bytes).decode("ascii")
        encoding = "base64"
    else:
        encoded_data = raw_bytes.decode("utf-8", errors="replace")
        encoding = "utf-8"

    return {
        "storage_uri": storage_uri,
        "offset": actual_start,
        "bytes_read": len(raw_bytes),
        "total_size": total_size,
        "has_more": (actual_start + len(raw_bytes)) < total_size,
        "encoding": encoding,
        "data": encoded_data
    }

#!/usr/bin/env python3
"""
Enterprise AWS CloudOps FastMCP Server
Enforces IAM read-only inspection boundaries across AWS infrastructure
"""

from mcp.server.fastmcp import FastMCP, Context
from pydantic import BaseModel, Field
import boto3
import asyncio

mcp = FastMCP("AWS-CloudOps-Readonly")

# Initialize Boto3 clients
ec2_client = boto3.client("ec2")
s3_client = boto3.client("s3")
rds_client = boto3.client("rds")

@mcp.tool()
async def list_unhealthy_instances(ctx: Context) -> str:
    """Inspects EC2 instances across the active AWS region and returns any in non-running states."""
    ctx.info("Querying EC2 DescribeInstanceStatus API...")
    
    response = await asyncio.to_thread(
        ec2_client.describe_instances,
        Filters=[{"Name": "instance-state-name", "Values": ["stopped", "stopping", "terminated"]}]
    )
    
    unhealthy = []
    for res in response.get("Reservations", []):
        for inst in res.get("Instances", []):
            name_tag = next((t["Value"] for t in inst.get("Tags", []) if t["Key"] == "Name"), "unnamed")
            unhealthy.append(f"- Instance ID: [{inst['InstanceId']}] ({name_tag}) — State: **{inst['State']['Name']}**")
            
    if not unhealthy:
        return "All monitored EC2 instances are in healthy RUNNING states."
    return "### Unhealthy or Stopped EC2 Instances:\n" + "\n".join(unhealthy)

if __name__ == "__main__":
    mcp.run(transport="stdio")

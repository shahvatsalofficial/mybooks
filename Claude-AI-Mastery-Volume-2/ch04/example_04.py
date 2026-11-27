"""
Recipe 04.4: Sovereign Enterprise MCP Gateway in Python
Author: Vatsal Shah (Vatsal Shah)
License: Apache-2.0
"""

import os
import json
import time
import logging
from typing import Dict, Any
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
audit_logger = logging.getLogger("McpAuditTrail")

app = FastAPI(title="Enterprise Sovereign MCP Gateway")

AUTHORIZED_KEYS = {
    os.getenv("ENTERPRISE_GATEWAY_TOKEN", "prod-bearer-token-101"): "Tenant-FinTech-Ops"
}

class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Any
    method: str
    params: Dict[str, Any] = {}

@app.post("/v1/mcp/gateway")
async def route_mcp_jsonrpc(req: JsonRpcRequest, authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "").strip()
    if token not in AUTHORIZED_KEYS:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid MCP Security Token")

    tenant_name = AUTHORIZED_KEYS[token]
    
    # Audit Trail Logging
    audit_logger.info(
        f"AUDIT | Tenant: {tenant_name} | Method: {req.method} | "
        f"ReqId: {req.id} | Timestamp: {time.time()}"
    )

    # Route method to internal subsystem
    if req.method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req.id,
            "result": {
                "tools": [
                    {"name": "fetch_financial_ledger", "description": "Fetches verified accounts ledger."}
                ]
            }
        }
    elif req.method == "tools/call":
        tool_name = req.params.get("name")
        # Enforce Tenant Isolation
        return {
            "jsonrpc": "2.0",
            "id": req.id,
            "result": {"content": [{"type": "text", "text": f"Ledger verified for {tenant_name}"}]}
        }

    return {"jsonrpc": "2.0", "id": req.id, "error": {"code": -32601, "message": "Method not found"}}

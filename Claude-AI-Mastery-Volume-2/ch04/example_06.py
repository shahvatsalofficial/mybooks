# Production Patch: Mandatory OAuth2 Token Authentication for Remote MCP SSE
import os
from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI(title="Hardened Enterprise MCP Server")
security = HTTPBearer()

EXPECTED_TOKEN = os.getenv("ENTERPRISE_MCP_AUTH_TOKEN")

async def verify_mcp_auth(credentials: HTTPAuthorizationCredentials = Security(security)):
    if not EXPECTED_TOKEN or credentials.credentials != EXPECTED_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid MCP Bearer Token")
    return credentials.credentials

@app.get("/sse", dependencies=[Depends(verify_mcp_auth)])
async def authenticated_sse_endpoint():
    # Only authenticated callers can establish SSE stream
    pass

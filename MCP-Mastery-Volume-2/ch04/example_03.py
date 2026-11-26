"""
Dynamic OpenAPI 3.1 to FastMCP Automated Bridge
Author: Vatsal Shah | Opportunity4u Press
Runtime: Python 3.11+ with FastMCP & httpx
"""

import json
import logging
from typing import Dict, Any, Optional
import httpx
from mcp.server.fastmcp import FastMCP, Context
from mcp.shared.exceptions import McpError
from mcp.types import ErrorCode

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("mcp.bridge.openapi")

class OpenApiToolBridge:
    """Ingests OpenAPI 3.1 specs and registers dynamic MCP tools."""

    def __init__(self, spec: Dict[str, Any], base_url: str, bearer_token: Optional[str] = None):
        self.spec = spec
        self.base_url = base_url.rstrip("/")
        self.bearer_token = bearer_token
        self.client = httpx.AsyncClient(timeout=10.0, follow_redirects=True)

    def _resolve_schema(self, schema_node: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively resolve local $ref pointers in JSON schema."""
        if "$ref" in schema_node:
            ref_path = schema_node["$ref"]
            if ref_path.startswith("#/components/schemas/"):
                schema_name = ref_path.split("/")[-1]
                target_schema = self.spec.get("components", {}).get("schemas", {}).get(schema_name, {})
                return self._resolve_schema(target_schema)
        
        resolved = {}
        for k, v in schema_node.items():
            if k.startswith("x-"):  # Strip vendor extensions to save tokens
                continue
            if isinstance(v, dict):
                resolved[k] = self._resolve_schema(v)
            elif isinstance(v, list):
                resolved[k] = [self._resolve_schema(item) if isinstance(item, dict) else item for item in v]
            else:
                resolved[k] = v
        return resolved

    def register_tools(self, mcp_server: FastMCP):
        """Parse OpenAPI paths and register corresponding MCP tools."""
        paths = self.spec.get("paths", {})
        for path_url, path_item in paths.items():
            for method, operation in path_item.items():
                if method.lower() not in ("get", "post", "put", "delete", "patch"):
                    continue

                op_id = operation.get("operationId")
                if not op_id:
                    clean_path = path_url.replace("/", "_").replace("{", "").replace("}", "")
                    op_id = f"{method.lower()}{clean_path}"

                # Sanitize tool name for MCP (alphanumeric and underscores)
                tool_name = op_id.replace("-", "_").lower()
                description = operation.get("summary") or operation.get("description") or f"Execute {method.upper()} {path_url}"

                # Extract requestBody JSON Schema
                req_body = operation.get("requestBody", {})
                json_content = req_body.get("content", {}).get("application/json", {})
                input_schema = self._resolve_schema(json_content.get("schema", {"type": "object", "properties": {}}))

                logger.info(f"Registering dynamic OpenAPI tool: {tool_name} [{method.upper()} {path_url}]")

                # Create closure for execution handler
                def make_handler(m: str, p: str):
                    async def dynamic_handler(ctx: Context, **kwargs) -> str:
                        target_url = f"{self.base_url}{p}"
                        headers = {"Content-Type": "application/json"}
                        if self.bearer_token:
                            headers["Authorization"] = f"Bearer {self.bearer_token}"

                        # Substitute path parameters if present
                        for param_key, param_val in list(kwargs.items()):
                            placeholder = f"{{{param_key}}}"
                            if placeholder in target_url:
                                target_url = target_url.replace(placeholder, str(param_val))
                                del kwargs[param_key]

                        try:
                            if m.lower() in ("get", "delete"):
                                response = await self.client.request(m.upper(), target_url, params=kwargs, headers=headers)
                            else:
                                response = await self.client.request(m.upper(), target_url, json=kwargs, headers=headers)

                            response.raise_for_status()
                            return response.text
                        except httpx.HTTPStatusError as hse:
                            logger.error(f"Upstream HTTP error on {target_url}: {hse.response.status_code}")
                            raise McpError(ErrorCode.InternalError, f"Upstream API Error {hse.response.status_code}: {hse.response.text}")
                        except Exception as ex:
                            logger.error(f"Connection failure on {target_url}: {str(ex)}")
                            raise McpError(ErrorCode.InternalError, f"Failed to connect to upstream service: {str(ex)}")

                    return dynamic_handler

                # Bind tool dynamically to FastMCP
                mcp_server.add_tool(
                    fn=make_handler(method, path_url),
                    name=tool_name,
                    description=description
                )


# Initialization Example
SAMPLE_OPENAPI_SPEC = {
    "openapi": "3.1.0",
    "info": { "title": "Customer Billing Service", "version": "1.0.0" },
    "paths": {
        "/customers/{customer_id}/invoices": {
            "get": {
                "operationId": "get_customer_invoices",
                "summary": "Retrieve paginated list of customer billing invoices",
                "parameters": [
                    { "name": "customer_id", "in": "path", "required": True, "schema": { "type": "string" } },
                    { "name": "status", "in": "query", "schema": { "type": "string", "enum": ["PAID", "DUE", "VOID"] } }
                ]
            }
        }
    }
}

mcp = FastMCP("Enterprise-OpenAPI-Bridge")
bridge = OpenApiToolBridge(SAMPLE_OPENAPI_SPEC, base_url="https://api.internal.enterprise.com", bearer_token="vault_injected_token")
bridge.register_tools(mcp)

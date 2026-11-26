class MCPToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]

class MockMCPClient:
    def __init__(self, server_url: str):
        self.server_url = server_url

    def discover_tools(self) -> List[MCPToolDefinition]:
        """Queries MCP server over JSON-RPC 2.0 to discover capabilities."""
        print(f"[MCP CLIENT] Discovering tools from {self.server_url}...")
        return [
            MCPToolDefinition(
                name="query_git_diff",
                description="Fetches git diff between two commit hashes.",
                input_schema={"base_commit": "str", "target_commit": "str"}
            )
        ]

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        print(f"[MCP CLIENT] Invoking '{tool_name}' via JSON-RPC 2.0...")
        return {"diff": "+ def secure_auth(): pass"}

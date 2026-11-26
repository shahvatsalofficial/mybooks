class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[str, int]
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

class EnterpriseMCPServer:
    def __init__(self):
        self.tools: Dict[str, Callable] = {}

    def register_tool(self, name: str, fn: Callable):
        self.tools[name] = fn

    def handle_rpc_request(self, raw_json_str: str) -> str:
        try:
            req = json.loads(raw_json_str)
            method = req.get("method")
            params = req.get("params", {})
            req_id = req.get("id")

            if method == "tools/list":
                tool_list = [{"name": k, "description": f"Tool {k}"} for k in self.tools]
                return JSONRPCResponse(id=req_id, result={"tools": tool_list}).model_dump_json()
                
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                if tool_name not in self.tools:
                    return JSONRPCResponse(id=req_id, error={"code": -32601, "message": "Method not found"}).model_dump_json()
                output = self.tools[tool_name](**tool_args)
                return JSONRPCResponse(id=req_id, result={"content": [{"type": "text", "text": str(output)}]}).model_dump_json()
                
            return JSONRPCResponse(id=req_id, error={"code": -32600, "message": "Invalid Request"}).model_dump_json()
        except Exception as exc:
            return JSONRPCResponse(id=None, error={"code": -32700, "message": f"Parse error: {exc}"}).model_dump_json()

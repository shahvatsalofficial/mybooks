class JSONRPCClientToolAdapter:
    def __init__(self, server_name: str):
        self.server_name = server_name
        self.msg_counter = 0

    def format_request(self, method: str, params: Dict[str, Any]) -> str:
        self.msg_counter += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self.msg_counter,
            "method": method,
            "params": params
        }
        return json.dumps(payload)

    def parse_response(self, raw_json: str) -> Dict[str, Any]:
        resp = json.loads(raw_json)
        if "error" in resp:
            err = resp["error"]
            raise RuntimeError(f"JSON-RPC Error {err.get('code')}: {err.get('message')}")
        return resp.get("result", {})

# Verification
adapter = JSONRPCClientToolAdapter("postgres-gateway")
req_payload = adapter.format_request("tools/call", {"name": "query_tables", "arguments": {"schema": "public"}})
print("Formatted JSON-RPC Request:", req_payload)
parsed = adapter.parse_response('{"jsonrpc": "2.0", "id": 1, "result": {"tables": ["users", "orders"]}}')
print("Parsed RPC Result:", parsed)

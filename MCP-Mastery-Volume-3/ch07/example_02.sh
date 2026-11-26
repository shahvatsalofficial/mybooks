# 1. Active Version Request (v2.1.0) — Returns 200 OK
curl -X POST http://localhost:8080/mcp/v1 \
  -H "Content-Type: application/json" \
  -H "Accept-MCP-Version: 2.1.0" \
  -H "X-Client-Application: trading-bot" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"crm:lookup_customer","arguments":{"customer_id":"CUST-849201"}}}'

# 2. Deprecated Version Request (v2.0.0) — Returns 200 OK with Sunset & Deprecation headers
curl -i -X POST http://localhost:8080/mcp/v1 \
  -H "Content-Type: application/json" \
  -H "Accept-MCP-Version: 2.0.0" \
  -H "X-Client-Application: legacy-agent" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"crm:lookup_customer","arguments":{"customer_id":"CUST-849201"}}}'

# 3. EOL Version Request (v1.0.0) — Returns 410 Gone with Error -32001 and Link header
curl -i -X POST http://localhost:8080/mcp/v1 \
  -H "Content-Type: application/json" \
  -H "Accept-MCP-Version: 1.0.0" \
  -H "X-Client-Application: ancient-worker" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"crm:lookup_customer","arguments":{"custId":"CUST-849201"}}}'

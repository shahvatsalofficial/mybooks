#!/usr/bin/env python3
import sys
import json

def log_diagnostic(msg: str):
    # Strict rule: ALWAYS write non-protocol logs to stderr!
    sys.stderr.write(f"[PYTHON-MCP] {msg}\n")
    sys.stderr.flush()

def send_response(response_obj: dict):
    payload = json.dumps(response_obj)
    sys.stdout.write(payload + "\n")
    sys.stdout.flush()  # CRITICAL: Prevent unbuffered pipe deadlocks!

def main():
    log_diagnostic("Starting raw STDIO MCP Server daemon...")
    
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
            
        try:
            req = json.loads(line)
        except Exception as e:
            log_diagnostic(f"Malformed JSON received: {e}")
            continue
            
        method = req.get("method")
        msg_id = req.get("id")
        
        # 1. Handle initialize handshake
        if method == "initialize":
            send_response({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": True}
                    },
                    "serverInfo": {"name": "raw-python-tracer", "version": "1.0.0"}
                }
            })
        elif method == "notifications/initialized":
            log_diagnostic("Handshake completed successfully by client.")
        elif method == "tools/list":
            send_response({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {
                            "name": "calculate_hash",
                            "description": "Computes SHA-256 cryptographic checksum of input payload",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "data": {"type": "string"}
                                },
                                "required": ["data"]
                            }
                        }
                    ]
                }
            })
        elif method == "tools/call":
            tool_name = req.get("params", {}).get("name")
            args = req.get("params", {}).get("arguments", {})
            
            if tool_name == "calculate_hash":
                import hashlib
                computed = hashlib.sha256(args.get("data", "").encode("utf-8")).hexdigest()
                send_response({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": f"SHA256: {computed}"}],
                        "isError": False
                    }
                })
            else:
                send_response({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
                })

if __name__ == "__main__":
    main()

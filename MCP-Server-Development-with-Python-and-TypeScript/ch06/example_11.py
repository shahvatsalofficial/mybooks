"""
recipe_6_4_dual_transport_runner.py
Production deployment script supporting both stdio and network SSE transports.
"""

import sys
import argparse
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("DualTransportServer")


@mcp.tool()
def compute_hash(data: str) -> str:
    """Calculates SHA-256 hash of arbitrary input data."""
    import hashlib
    digest = hashlib.sha256(data.encode("utf-8")).hexdigest()
    return f"SHA256: {digest}"


def main():
    parser = argparse.ArgumentParser(description="Run FastMCP Server across transports.")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport protocol to bind (default: stdio)."
    )
    parser.add_argument("--host", default="127.0.0.1", help="Network host interface for SSE.")
    parser.add_argument("--port", type=int, default=8000, help="Network port for SSE.")

    args = parser.parse_args()

    if args.transport == "stdio":
        sys.stderr.write("[Server] Launching in STDIO mode for local desktop host...\n")
        mcp.run(transport="stdio")
    elif args.transport == "sse":
        sys.stderr.write(f"[Server] Launching in SSE mode on http://{args.host}:{args.port}/sse ...\n")
        # FastMCP embeds Starlette and Uvicorn to serve SSE and POST endpoints
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="sse")


if __name__ == "__main__":
    main()

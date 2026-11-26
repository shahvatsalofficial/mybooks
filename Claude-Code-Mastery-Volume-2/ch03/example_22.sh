# Launch FastMCP server with automatic hot-reloading on source file modifications
uv run watchfiles "python -u server.py" src/ --filter python

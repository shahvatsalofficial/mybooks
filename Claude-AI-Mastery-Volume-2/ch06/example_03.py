@mcp.resource("market://portfolio/{client_id}/positions")
async def get_client_positions(client_id: str) -> str:
    """Returns real-time equity holdings and cash balances for a designated client account."""
    positions = await db_client.fetch_positions(client_id)
    return json.dumps(positions, indent=2)

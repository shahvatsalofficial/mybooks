@mcp.tool()
async def track_container_status(container_id: str) -> str:
    # FLAW: Background task spawned without supervisor or error handling
    asyncio.create_task(emit_telemetry_webhook(container_id))
    return "Status recorded."

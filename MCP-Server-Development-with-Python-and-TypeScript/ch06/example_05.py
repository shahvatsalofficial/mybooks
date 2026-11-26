@mcp.tool()
async def long_running_analytics(dataset_id: str, ctx: Context) -> str:
    """Demonstrates cooperative cancellation check in long-running jobs."""
    for step in range(100):
        # Cooperatively check if user cancelled the generation
        if await ctx.session.is_cancelled():
            sys.stderr.write(f"[Server] Job {dataset_id} aborted by client cancellation.\n")
            return "Operation cancelled by user."
        
        await asyncio.sleep(0.5)  # Simulate non-blocking work chunk

    return f"Dataset {dataset_id} processed successfully."

from collections.abc import AsyncIterator

@mcp.tool()
async def stream_log_analysis(log_file_path: str, ctx: Context) -> AsyncIterator[str]:
    """Streams token-by-token log analysis as anomalies are discovered in real time."""
    ctx.info(f"Streaming analysis for {log_file_path}...")
    
    yield "### Real-Time Anomaly Stream Initiated
"
    
    # Simulate streaming anomaly detections
    anomalies = [
        "Anomaly 1 [14:02:11]: Socket timeout in connection pool worker-04",
        "Anomaly 2 [14:02:15]: Spike in HTTP 504 Gateway Timeouts on /api/v1/checkout",
        "Anomaly 3 [14:02:19]: Deadlock detected in PostgreSQL transaction isolation barrier"
    ]
    
    for anomaly in anomalies:
        await asyncio.sleep(0.4)
        yield f"- {anomaly}
"
        
    yield "
**Analysis Complete:** 3 critical anomalies detected."

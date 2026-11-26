# REMEDIATED ASYNCHRONOUS ROUTE HANDLER
@app.post("/api/v1/settle")
async def process_settlement(payload: SettlementRequest):
    try:
        # Offload synchronous C-extension network lookup to worker thread pool
        geo_data = await asyncio.wait_for(
            asyncio.to_thread(geoip_client.lookup, payload.client_ip),
            timeout=0.200,  # Strict 200ms circuit breaker timeout
        )
    except (asyncio.TimeoutError, Exception) as exc:
        logger.warning("Geolocation lookup failed or timed out: %s. Using default fallback.", exc)
        geo_data = DEFAULT_FALLBACK_GEO
    
    # Event loop remains 100% fluid and responsive
    result = await payment_core.execute(payload, geo_data)
    return result

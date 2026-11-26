# DEFECTIVE LEGACY ROUTE HANDLER (PRE-INCIDENT)
@app.post("/api/v1/settle")
async def process_settlement(payload: SettlementRequest):
    # CRITICAL ARCHITECTURAL FLAW:
    # 'geoip_client.lookup()' was a synchronous C-extension that made a blocking 
    # network call to a remote MaxMind database over TCP with a 2.5-second timeout!
    geo_data = geoip_client.lookup(payload.client_ip)  # <--- BLOCKS ENTIRE UVLOOP!
    
    # Process settlement asynchronously...
    result = await payment_core.execute(payload, geo_data)
    return result

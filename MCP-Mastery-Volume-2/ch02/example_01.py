# CATASTROPHIC ANTI-PATTERN: DO NOT EVER DO THIS IN PRODUCTION
current_tenant_id = None

@app.post("/messages")
async def handle_message(request: Request):
    global current_tenant_id
    # Request from Tenant A arrives
    current_tenant_id = request.headers.get("X-Tenant-ID")  # "tenant_alpha"
    
    # Coroutine yields execution here while waiting for slow database query!
    await asyncio.sleep(0.050)  
    
    # In the meantime, Request from Tenant B arrives and overwrites global variable!
    # current_tenant_id is now "tenant_beta"
    
    # Tenant A's coroutine resumes, but now reads Tenant B's identity!
    return await execute_tool(current_tenant_id)  # DISASTROUS DATA LEAK

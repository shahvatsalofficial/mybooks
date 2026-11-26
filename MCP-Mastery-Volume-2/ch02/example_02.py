# FLAWED STREAMING PATTERN: Leaking Context Across Stream Ticks
async def stream_tenant_records(query: str):
    token = CURRENT_TENANT_ID.set(extract_tenant_from_request())
    try:
        async for row in execute_cursor(query):
            yield row  # Suspends here! Token remains active during client network pauses!
    finally:
        CURRENT_TENANT_ID.reset(token)

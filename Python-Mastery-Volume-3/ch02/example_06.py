# DISASTROUS ANTI-PATTERN: Client instantiation per request
@app.get("/api/v1/aggregate")
async def aggregate_data():
    async with httpx.AsyncClient() as client:  # <--- FATAL FLAW!
        resp = await client.get("https://downstream.internal/data")
        return resp.json()

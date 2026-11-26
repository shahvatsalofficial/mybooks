# DEFECTIVE PRODUCTION CODE (Pre-Incident)
async def dispatch_webhook(event_payload: dict, webhook_url: str) -> None:
    # FATAL DEFECT: Instantiating AsyncClient inside the coroutine!
    async with httpx.AsyncClient(timeout=5.0) as client:
        await client.post(webhook_url, json=event_payload)
        # Sockets are closed actively upon block exit, entering TIME_WAIT!

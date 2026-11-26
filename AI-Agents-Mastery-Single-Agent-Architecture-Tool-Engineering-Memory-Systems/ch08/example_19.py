import httpx

async def call_model_provider_with_deadline(url: str, payload: Dict[str, Any], deadline_sec: float = 10.0) -> Dict[str, Any]:
    timeout = httpx.Timeout(deadline_sec, connect=2.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            # Immediate fast-fail trigger
            raise TimeoutError(f"Fast-Fail Gate: Upstream provider exceeded {deadline_sec}s deadline.")

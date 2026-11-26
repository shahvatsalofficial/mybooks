async def fetch_order(order_id: int) -> dict:
    return {"order_id": order_id}

res = fetch_order(101) # Does NOT return dict! Returns <coroutine object at 0x7f...>

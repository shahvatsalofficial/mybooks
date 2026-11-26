# THE UNSTRUCTURED CONCURRENCY DISASTER (Pre-Python 3.11 Anti-Pattern)
async def handle_request():
    t1 = asyncio.create_task(query_user_db())
    t2 = asyncio.create_task(query_payment_gateway())
    
    # If query_payment_gateway() raises an exception, gather raises immediately...
    res = await asyncio.gather(t1, t2)
    return res

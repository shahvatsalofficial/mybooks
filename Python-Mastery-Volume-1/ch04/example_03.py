# THE MODERN STRUCTURED CONCURRENCY PATTERN (Python 3.11+)
async def handle_request_structured():
    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(query_user_db())
        t2 = tg.create_task(query_payment_gateway())
        t3 = tg.create_task(write_audit_log())
    
    # Execution ONLY reaches this line when t1, t2, and t3 have completely finished!
    return t1.result(), t2.result()

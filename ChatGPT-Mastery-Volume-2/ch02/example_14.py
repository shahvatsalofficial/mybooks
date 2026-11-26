# CATASTROPHIC ANTI-PATTERN
async def fetch_customer_orders(order_query_sql: str):
    # DIRECT EXECUTION OF UNTRUSTED LLM GENERATED SQL
    return await db.execute(order_query_sql)

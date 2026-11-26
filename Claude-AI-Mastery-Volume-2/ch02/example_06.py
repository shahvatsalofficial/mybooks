# FLAWED PRODUCTION CODE: Unbounded parallel execution
tasks = [execute_db_lookup(block["input"]["container_id"]) for block in tool_calls]
results = await asyncio.gather(*tasks) # Launches 450 concurrent tasks!

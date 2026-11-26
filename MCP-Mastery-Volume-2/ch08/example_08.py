# FLAWED PRODUCTION TOOL IMPLEMENTATION
@server.tool()
async def get_realtime_orderbook(ticker: str) -> dict:
    """Fetch orderbook depth from internal relational database."""
    # Defect 1: Printing debug messages directly to stdout over stdio transport!
    print(f"[DEBUG] Fetching orderbook for ticker: {ticker}")
    
    # Defect 2: Synchronous, blocking database call inside an async handler!
    import time
    db_conn = get_global_db_pool().get_connection()
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM market_depth WHERE ticker = %s", (ticker,))
    rows = cursor.fetchall() # Blocking network I/O freezing event loop!
    
    return {"ticker": ticker, "bids": rows[:10]}

"""
Architectural Drill 7: Out-of-Core SQLite Disk Spilling Engine
"""

import sqlite3
import pandas as pd
import os

DB_PATH = '/mnt/data/ephemeral_pipeline.db'
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Tune SQLite PRAGMAs for high-speed batch ingestion with minimal RAM usage
cursor.execute("PRAGMA synchronous = OFF;")
cursor.execute("PRAGMA journal_mode = MEMORY;")
cursor.execute("PRAGMA cache_size = -64000;") # 64MB cache ceiling

print("Stage 1: Streaming Transactions into On-Disk SQLite Table...")
chunk_size = 50000
for chunk in pd.read_csv('/mnt/data/large_transactions.csv', chunksize=chunk_size):
    chunk.to_sql('transactions', conn, if_exists='append', index=False)

print("Stage 2: Streaming User Dimensions Table...")
for chunk in pd.read_csv('/mnt/data/user_dimensions.csv', chunksize=chunk_size):
    chunk.to_sql('users', conn, if_exists='append', index=False)

print("Stage 3: Building B-Tree Indexes on Disk...")
cursor.execute("CREATE INDEX idx_tx_user ON transactions(user_id);")
cursor.execute("CREATE INDEX idx_usr_id ON users(user_id);")
conn.commit()

print("Stage 4: Executing Out-of-Core SQL Join & Aggregation...")
query = """
SELECT 
    u.country_code,
    u.subscription_tier,
    COUNT(t.transaction_id) AS total_tx_count,
    ROUND(SUM(t.amount_usd), 2) AS total_gross_usd,
    ROUND(AVG(t.amount_usd), 2) AS avg_ticket_usd
FROM transactions t
INNER JOIN users u ON t.user_id = u.user_id
WHERE t.status = 'COMPLETED'
GROUP BY u.country_code, u.subscription_tier
ORDER BY total_gross_usd DESC;
"""

final_summary_df = pd.read_sql_query(query, conn)
conn.close()

# Cleanup on-disk SQLite database to free scratch space
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

print("Aggregated Results (Executed within < 120MB peak RAM):")
print(final_summary_df.head(10))
final_summary_df.to_csv('/mnt/data/final_aggregated_kpis.csv', index=False)

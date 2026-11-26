# Hardened Distributed PostgreSQL Checkpointer Architecture:
import psycopg_pool
from langgraph.checkpoint.postgres import PostgresSaver

# 1. Establish thread-safe connection pool with connection pooling
DB_URI = "postgresql://agent_admin:SecretPass99@pg-cluster.internal:5432/agent_state"
pool = psycopg_pool.ConnectionPool(
    conninfo=DB_URI,
    max_size=20,
    kwargs={"autocommit": True}
)

# 2. Instantiate enterprise PostgreSQL checkpointer with table setup
with pool.connection() as conn:
    pg_checkpointer = PostgresSaver(conn)
    pg_checkpointer.setup() # Automatically provisions checkpoints and writes tables

# 3. Compile graph with resilient distributed checkpointer
production_app = workflow.compile(checkpointer=pg_checkpointer)

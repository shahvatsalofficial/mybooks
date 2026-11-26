import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

# Setup persistent SQLite checkpointer on disk
db_path = "checkpoints_store.db"
conn = sqlite3.connect(db_path, check_same_thread=False)
checkpointer = SqliteSaver(conn)

# Compile graph with checkpointer bound
persisted_app = workflow.compile(checkpointer=checkpointer)

# Configuration with persistent session thread_id
thread_config = {"configurable": {"thread_id": "session_enterprise_9021"}}

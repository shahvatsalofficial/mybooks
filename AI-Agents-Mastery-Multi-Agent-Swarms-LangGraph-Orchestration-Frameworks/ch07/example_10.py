def generate_postgres_ddl() -> str:
    return """
    CREATE TABLE IF NOT EXISTS agent_thread_checkpoints (
        checkpoint_id UUID PRIMARY KEY,
        thread_id VARCHAR(128) NOT NULL,
        version INT NOT NULL DEFAULT 1,
        state_json JSONB NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        CONSTRAINT uq_thread_version UNIQUE (thread_id, version)
    );
    CREATE INDEX IF NOT EXISTS idx_thread_id ON agent_thread_checkpoints(thread_id);
    """

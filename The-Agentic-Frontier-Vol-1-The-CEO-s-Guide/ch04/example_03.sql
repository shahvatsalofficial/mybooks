CREATE TABLE agent_executions (
    execution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id VARCHAR(255) NOT NULL,
    manifest_version VARCHAR(50) NOT NULL,
    trigger_source VARCHAR(100), -- 'webhook', 'schedule', 'manual'
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20), -- 'success', 'failed', 'quarantined'
    raw_input JSONB,
    reasoning_chain JSONB, -- Array of internal thought steps
    tool_calls JSONB, -- Array of API requests/responses
    validator_output JSONB, -- Results of Syntactic/Semantic/Deterministic checks
    ler_score FLOAT, -- Logic Error Rate for this execution
    audit_hash VARCHAR(64) UNIQUE -- SHA-256 hash for immutability
);

CREATE INDEX idx_ler_threshold ON agent_executions (ler_score) WHERE ler_score > 0.1;

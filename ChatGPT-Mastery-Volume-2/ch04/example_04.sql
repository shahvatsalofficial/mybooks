-- Enterprise pgvector Schema with HNSW Index & RLS
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Create Partitioned Documents Table
CREATE TABLE enterprise_knowledge_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(64) NOT NULL,
    department VARCHAR(64) NOT NULL,
    document_title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- Matryoshka-sliced 1024-dimensional embedding vector
    embedding vector(1024) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Construct High-Performance HNSW Vector Index
CREATE INDEX idx_knowledge_chunks_hnsw_cosine 
ON enterprise_knowledge_chunks 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 3. Construct Inverted Index for JSONB Metadata Filtering
CREATE INDEX idx_knowledge_chunks_metadata ON enterprise_knowledge_chunks USING GIN (metadata);

-- 4. Enforce Kernel-Level Row-Level Security (RLS)
ALTER TABLE enterprise_knowledge_chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_policy ON enterprise_knowledge_chunks
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true));

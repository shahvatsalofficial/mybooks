-- 1. Create dedicated locked-down application role for MCP bridge
CREATE ROLE mcp_agent_readonly WITH LOGIN PASSWORD 'secure_entropy_pass' NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;

-- 2. Revoke all ambient permissions on database and public schema
REVOKE ALL ON DATABASE analytics_warehouse FROM mcp_agent_readonly;
REVOKE ALL ON SCHEMA public FROM mcp_agent_readonly;

-- 3. Grant strict CONNECT and USAGE on target analytical schemas
GRANT CONNECT ON DATABASE analytics_warehouse TO mcp_agent_readonly;
GRANT USAGE ON SCHEMA enterprise_data TO mcp_agent_readonly;

-- 4. Grant SELECT strictly on existing and future tables
GRANT SELECT ON ALL TABLES IN SCHEMA enterprise_data TO mcp_agent_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA enterprise_data GRANT SELECT ON TABLES TO mcp_agent_readonly;

-- 5. Hard-lock connection settings to prevent side-channel abuse
ALTER ROLE mcp_agent_readonly SET default_transaction_read_only = on;
ALTER ROLE mcp_agent_readonly SET statement_timeout = '3000ms';
ALTER ROLE mcp_agent_readonly SET lock_timeout = '1000ms';

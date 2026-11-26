-- Enforced on every connection checkout in the MCP pool
SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY;
SET statement_timeout = '3000ms';
SET idle_in_transaction_session_timeout = '5000ms';
SET work_mem = '16MB';

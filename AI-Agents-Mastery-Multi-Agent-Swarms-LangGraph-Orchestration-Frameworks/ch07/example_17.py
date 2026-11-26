PG_ADVISORY_LOCK_SQL = """
-- 1. Acquire transaction-level advisory lock on 64-bit integer hash of session_id
BEGIN;
SELECT pg_advisory_xact_lock(hashtext('session_enterprise_9912'));

-- 2. Execute agent state modifications with guaranteed cross-process exclusion
UPDATE agent_checkpoints 
SET state_payload = '{"status": "AUTHORIZED"}' 
WHERE thread_id = 'session_enterprise_9912';

-- 3. Lock is automatically and reliably released upon COMMIT
COMMIT;
"""

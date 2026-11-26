SQL_ROW_LEVEL_LOCK_TRANSACTION = """
-- 1. Begin atomic database transaction
BEGIN;

-- 2. Lock target thread row; concurrent transactions will block until COMMIT
SELECT checkpoint_id, thread_id, state_payload, version 
FROM agent_checkpoints 
WHERE thread_id = 'session_enterprise_9912' 
FOR UPDATE;

-- 3. Execute state modification
UPDATE agent_checkpoints 
SET state_payload = '{"status": "APPROVED"}', 
    version = version + 1, 
    updated_at = NOW() 
WHERE thread_id = 'session_enterprise_9912';

-- 4. Commit transaction and release row lock
COMMIT;
"""

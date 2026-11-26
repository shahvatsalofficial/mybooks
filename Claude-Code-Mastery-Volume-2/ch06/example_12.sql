-- Mandatory Idempotent Migration Standard for Autonomous Agents
DO $
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='users' AND column_name='loyalty_points'
    ) THEN
        ALTER TABLE users ADD COLUMN loyalty_points INT DEFAULT 0 NOT NULL;
    END IF;
END $;

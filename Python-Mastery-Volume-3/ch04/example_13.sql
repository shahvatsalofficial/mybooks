-- REMEDIATED ZERO-DOWNTIME MIGRATION
SET lock_timeout = '2000ms';
ALTER TABLE accounts ADD COLUMN account_tier VARCHAR(32);
-- Backfill executed in batches...
-- Enforce constraint safely:
ALTER TABLE accounts ADD CONSTRAINT chk_account_tier_not_null CHECK (account_tier IS NOT NULL) NOT VALID;
ALTER TABLE accounts VALIDATE CONSTRAINT chk_account_tier_not_null;

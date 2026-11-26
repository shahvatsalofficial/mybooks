ALTER TABLE ledger_entries ADD COLUMN idempotency_hash VARCHAR(64) NOT NULL;

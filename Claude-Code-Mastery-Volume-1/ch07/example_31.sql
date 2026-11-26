-- Emergency Remedial Migration: V4.12.9__restore_orders_index.sql
-- CONCURRENTLY ensures zero table locking during index construction
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_user_created 
ON orders (user_id, created_at DESC);

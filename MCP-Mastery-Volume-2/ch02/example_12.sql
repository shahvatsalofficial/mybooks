-- INSUFFICIENT: Index on order_date alone requires scanning across all tenants
CREATE INDEX idx_orders_date ON customer_orders (order_date);

-- PRODUCTION STANDARD: Composite index leads with tenant_id
CREATE INDEX idx_orders_tenant_date ON customer_orders (tenant_id, order_date DESC);

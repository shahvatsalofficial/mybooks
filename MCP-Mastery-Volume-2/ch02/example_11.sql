BEGIN;
SELECT set_config('app.current_tenant_id', 'tenant_alpha', true);
-- All subsequent queries within this transaction are automatically scoped
SELECT * FROM customer_invoices WHERE status = 'OVERDUE';
COMMIT;

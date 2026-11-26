CREATE POLICY mcp_tenant_isolation_policy ON customer_invoices
    FOR ALL
    TO mcp_app_role
    USING (tenant_id = current_setting('app.current_tenant_id', true))
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true));

-- The Fatal Unbounded Query
SELECT * 
FROM customers c 
JOIN invoices i ON c.id = i.customer_id 
JOIN audit_logs a ON a.entity_id = c.id;

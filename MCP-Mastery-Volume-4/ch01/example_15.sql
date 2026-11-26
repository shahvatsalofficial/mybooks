SELECT id, transaction_amount, created_at 
FROM transactions 
ORDER BY id ASC 
LIMIT 50 OFFSET 100000;

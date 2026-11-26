SELECT product_id, sku, title, price, (embedding <=> $1) AS cosine_distance
FROM catalog_products
WHERE tenant_id = $2 AND status = 'IN_STOCK' AND price <= $3
ORDER BY cosine_distance ASC
LIMIT 20;

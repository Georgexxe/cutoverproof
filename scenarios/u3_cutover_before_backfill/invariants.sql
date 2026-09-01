-- Invariant for U3: returns any orders where status_id is NULL or mismatch
SELECT 
    o.id, 
    o.status AS legacy_status, 
    o.status_id, 
    os.name AS lookup_status
FROM orders o
LEFT JOIN order_statuses os ON o.status_id = os.id
WHERE o.status_id IS NULL OR o.status != os.name;

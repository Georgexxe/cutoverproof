-- Invariant for U2
SELECT 
    o.id, 
    o.status AS legacy_status, 
    o.status_id, 
    os.name AS lookup_status
FROM orders o
JOIN order_statuses os ON o.status_id = os.id
WHERE o.status != os.name;

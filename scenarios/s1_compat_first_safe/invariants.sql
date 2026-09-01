-- Invariant for S1: returns rows where status_id is populated but does not match status
SELECT 
    o.id, 
    o.status AS legacy_status, 
    o.status_id, 
    os.name AS lookup_status
FROM orders o
JOIN order_statuses os ON o.status_id = os.id
WHERE o.status != os.name;

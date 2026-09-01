-- Status Consistency Invariant Assertion
-- Returns any rows where status_id is non-null but does NOT match orders.status text
SELECT 
    o.id, 
    o.status AS legacy_status, 
    o.status_id, 
    os.name AS lookup_status
FROM orders o
JOIN order_statuses os ON o.status_id = os.id
WHERE o.status != os.name;

-- Invariant for S2
SELECT 
    o.id, 
    o.status, 
    o.status_id, 
    v.resolved_status 
FROM orders o 
JOIN v_orders_compat v ON o.id = v.id 
WHERE o.status_id IS NOT NULL AND o.status != v.resolved_status;

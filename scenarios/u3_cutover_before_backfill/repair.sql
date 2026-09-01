-- Repair for U3: Complete full backfill across all rows
UPDATE orders o 
SET status_id = s.id 
FROM order_statuses s 
WHERE o.status = s.name AND o.status_id IS NULL;

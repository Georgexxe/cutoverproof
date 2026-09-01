-- Expand Schema for S2 with Compatibility View
CREATE TABLE IF NOT EXISTS order_statuses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(32) UNIQUE NOT NULL
);

INSERT INTO order_statuses (id, name) VALUES
    (1, 'pending'),
    (2, 'paid'),
    (3, 'shipped'),
    (4, 'refunded')
ON CONFLICT (id) DO NOTHING;

ALTER TABLE orders ADD COLUMN IF NOT EXISTS status_id INT REFERENCES order_statuses(id);

CREATE OR REPLACE VIEW v_orders_compat AS 
SELECT 
    o.id, 
    o.customer_id, 
    o.total_amount, 
    COALESCE(os.name, o.status) AS resolved_status, 
    o.status_id 
FROM orders o 
LEFT JOIN order_statuses os ON o.status_id = os.id;

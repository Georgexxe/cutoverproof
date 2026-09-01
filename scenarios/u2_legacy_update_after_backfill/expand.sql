-- Expand for U2
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

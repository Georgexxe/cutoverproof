-- Schema for S1 (Safe control)
CREATE TABLE IF NOT EXISTS orders (
    id INT PRIMARY KEY,
    customer_id INT NOT NULL,
    total_amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS payment_events (
    id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(id),
    event_type VARCHAR(32) NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION process_legacy_payment() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.event_type = 'payment_confirmed' THEN
        UPDATE orders SET status = 'paid' WHERE id = NEW.order_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_legacy_payment ON payment_events;
CREATE TRIGGER trg_legacy_payment
AFTER INSERT ON payment_events
FOR EACH ROW EXECUTE FUNCTION process_legacy_payment();

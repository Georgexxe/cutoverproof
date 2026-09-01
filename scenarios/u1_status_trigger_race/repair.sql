-- Repaired Migration Logic for U1
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

CREATE OR REPLACE FUNCTION process_legacy_payment() RETURNS TRIGGER AS '
DECLARE
    paid_status_id INT;
BEGIN
    IF NEW.event_type = ''payment_confirmed'' THEN
        SELECT id INTO paid_status_id FROM order_statuses WHERE name = ''paid'';
        UPDATE orders 
        SET status = ''paid'',
            status_id = COALESCE(paid_status_id, status_id)
        WHERE id = NEW.order_id;
    END IF;
    RETURN NEW;
END;
' LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_legacy_payment ON payment_events;
CREATE TRIGGER trg_legacy_payment
AFTER INSERT ON payment_events
FOR EACH ROW EXECUTE FUNCTION process_legacy_payment();

CREATE OR REPLACE FUNCTION sync_status_compat() RETURNS TRIGGER AS '
BEGIN
    IF NEW.status IS DISTINCT FROM OLD.status AND (NEW.status_id IS NOT DISTINCT FROM OLD.status_id) THEN
        SELECT id INTO NEW.status_id FROM order_statuses WHERE name = NEW.status;
    ELSIF NEW.status_id IS DISTINCT FROM OLD.status_id AND (NEW.status IS NOT DISTINCT FROM OLD.status) THEN
        SELECT name INTO NEW.status FROM order_statuses WHERE id = NEW.status_id;
    END IF;
    RETURN NEW;
END;
' LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_status ON orders;
CREATE TRIGGER trg_sync_status
BEFORE UPDATE OR INSERT ON orders
FOR EACH ROW EXECUTE FUNCTION sync_status_compat();

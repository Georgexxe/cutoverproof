-- Repair for U2: Install sync trigger before backfill
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

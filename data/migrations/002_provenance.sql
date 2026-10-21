-- SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
-- SPDX-License-Identifier: Apache-2.0

BEGIN;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'tickets_source_values') THEN
        ALTER TABLE tickets ADD CONSTRAINT tickets_source_values
            CHECK (source IN ('dx-helpdesk', 'snipe-it', 'nats'));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'attachments_source_values') THEN
        ALTER TABLE ticket_attachments ADD CONSTRAINT attachments_source_values
            CHECK (source IN ('dx-helpdesk', 'snipe-it', 'nats'));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'events_source_values') THEN
        ALTER TABLE ticket_events ADD CONSTRAINT events_source_values
            CHECK (source IN ('dx-helpdesk', 'snipe-it', 'nats'));
    END IF;
END $$;

CREATE OR REPLACE FUNCTION reject_ticket_event_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'ticket_events is append-only';
END;
$$;
DROP TRIGGER IF EXISTS ticket_events_append_only ON ticket_events;
CREATE TRIGGER ticket_events_append_only
    BEFORE UPDATE OR DELETE ON ticket_events
    FOR EACH ROW EXECUTE FUNCTION reject_ticket_event_mutation();

COMMIT;

-- SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
-- SPDX-License-Identifier: Apache-2.0

-- Upgrade an existing #16 database without losing the original asset tags.
BEGIN;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS location_id integer;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS asset_id integer CHECK (asset_id > 0);
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS co_so text CHECK (co_so IN ('CS1','CS2','CS3'));
CREATE TABLE IF NOT EXISTS site_locations (
    location_id integer PRIMARY KEY,
    code text NOT NULL UNIQUE,
    co_so text NOT NULL CHECK (co_so IN ('CS1','CS2','CS3'))
);
INSERT INTO site_locations (location_id, code, co_so) VALUES
    (1,'CS1','CS1'),(2,'CS1-TOA-C','CS1'),(3,'CS1-TOA-A10','CS1'),
    (4,'CS1-C-LAB301','CS1'),(5,'CS1-C-LAB302','CS1'),
    (6,'CS1-C-PM401','CS1'),(7,'CS1-C-PM402','CS1'),(8,'CS1-A10-MANG502','CS1'),
    (9,'CS2','CS2'),(10,'CS2-TOA-B1','CS2'),(11,'CS2-TOA-B2','CS2'),
    (12,'CS2-B1-PM201','CS2'),(13,'CS2-B1-PM202','CS2'),(14,'CS2-B2-LAB301','CS2'),
    (15,'CS3','CS3'),(16,'CS3-TOA-H1','CS3'),(17,'CS3-TOA-H2','CS3'),
    (18,'CS3-H1-PM301','CS3'),(19,'CS3-H1-PM302','CS3'),(20,'CS3-H2-LAB205','CS3')
ON CONFLICT (location_id) DO UPDATE SET code = EXCLUDED.code, co_so = EXCLUDED.co_so;
UPDATE tickets t SET location_id = l.location_id, co_so = l.co_so
FROM site_locations l WHERE t.location = l.code AND t.location_id IS NULL;
ALTER TABLE tickets DROP CONSTRAINT ticket_submitted_fields;
ALTER TABLE tickets ADD CONSTRAINT ticket_submitted_fields CHECK (
    status = 'DRAFT' OR (category IS NOT NULL AND priority IS NOT NULL AND
    submitted_at IS NOT NULL AND co_so IS NOT NULL)
) NOT VALID;
CREATE TABLE IF NOT EXISTS ticket_legacy_asset_refs (
    ticket_id uuid PRIMARY KEY REFERENCES tickets(id),
    asset_ref text NOT NULL
);
DO $$ BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'tickets' AND column_name = 'asset_ref') THEN
        INSERT INTO ticket_legacy_asset_refs (ticket_id, asset_ref)
        SELECT id, asset_ref FROM tickets WHERE asset_ref IS NOT NULL
        ON CONFLICT (ticket_id) DO NOTHING;
        ALTER TABLE tickets DROP COLUMN asset_ref;
    END IF;
END $$;
CREATE INDEX IF NOT EXISTS tickets_active_site_idx ON tickets (co_so, created_at DESC)
    WHERE deleted_at IS NULL;
COMMIT;

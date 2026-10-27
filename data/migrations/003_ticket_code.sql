-- SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
-- SPDX-License-Identifier: Apache-2.0

BEGIN;
CREATE SEQUENCE IF NOT EXISTS ticket_code_seq;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS code text;
ALTER TABLE tickets ALTER COLUMN code SET DEFAULT ('DXL-' || lpad(nextval('ticket_code_seq')::text, 4, '0'));
-- Existing tickets receive stable unique codes; sequence allocation is atomic for new tickets.
UPDATE tickets SET code = 'DXL-' || lpad(nextval('ticket_code_seq')::text, 4, '0')
WHERE code IS NULL;
ALTER TABLE tickets ALTER COLUMN code SET NOT NULL;
ALTER TABLE tickets ADD CONSTRAINT tickets_code_key UNIQUE (code);
COMMIT;

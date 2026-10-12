-- SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
-- SPDX-License-Identifier: Apache-2.0

-- Initial schema for the dxdata database. Keycloak subjects and Flowable process
-- instance IDs are external identifiers, so no cross-service foreign keys exist.
-- Apply once to an empty dxdata database; later changes require migrations.

BEGIN;

CREATE TABLE tickets (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    title text NOT NULL CHECK (length(btrim(title)) BETWEEN 1 AND 200),
    description text NOT NULL CHECK (length(btrim(description)) > 0),
    category text CHECK (category IN (
        'HARDWARE', 'SOFTWARE_ENVIRONMENT', 'NETWORK_ACCOUNT', 'LAB_ASSET'
    )),
    priority text CHECK (priority IN ('URGENT', 'HIGH', 'MEDIUM', 'LOW')),
    status text NOT NULL DEFAULT 'DRAFT' CHECK (status IN (
        'DRAFT', 'SUBMITTED', 'ASSIGNED', 'IN_PROGRESS',
        'RESOLVED', 'CLOSED', 'REJECTED'
    )),
    location text,
    asset_ref text,
    created_by text NOT NULL CHECK (length(btrim(created_by)) > 0),
    assigned_to text,
    source text NOT NULL DEFAULT 'dx-helpdesk' CHECK (length(btrim(source)) > 0),
    workflow_instance_id text UNIQUE,
    resolution_summary text,
    rejection_reason text,
    satisfaction_rating smallint CHECK (satisfaction_rating BETWEEN 1 AND 5),
    sla_due_at timestamptz,
    submitted_at timestamptz,
    resolved_at timestamptz,
    closed_at timestamptz,
    rejected_at timestamptz,
    deleted_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ticket_submitted_fields CHECK (
        status = 'DRAFT' OR (category IS NOT NULL AND priority IS NOT NULL AND submitted_at IS NOT NULL)
    ),
    CONSTRAINT ticket_assignment CHECK (
        status NOT IN ('ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'CLOSED') OR assigned_to IS NOT NULL
    ),
    CONSTRAINT ticket_resolution CHECK (
        status NOT IN ('RESOLVED', 'CLOSED') OR
        (resolution_summary IS NOT NULL AND length(btrim(resolution_summary)) > 0 AND resolved_at IS NOT NULL)
    ),
    CONSTRAINT ticket_closed_at CHECK (status <> 'CLOSED' OR closed_at IS NOT NULL),
    CONSTRAINT ticket_rejection CHECK (
        status <> 'REJECTED' OR
        (rejection_reason IS NOT NULL AND length(btrim(rejection_reason)) > 0 AND rejected_at IS NOT NULL)
    ),
    CONSTRAINT ticket_rating CHECK (satisfaction_rating IS NULL OR status = 'CLOSED'),
    CONSTRAINT ticket_soft_delete CHECK (deleted_at IS NULL OR status = 'DRAFT')
);

CREATE TABLE ticket_attachments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id uuid NOT NULL REFERENCES tickets(id),
    storage_key text NOT NULL UNIQUE CHECK (length(btrim(storage_key)) > 0),
    file_name text NOT NULL CHECK (length(btrim(file_name)) > 0),
    content_type text NOT NULL CHECK (length(btrim(content_type)) > 0),
    size_bytes bigint NOT NULL CHECK (size_bytes >= 0),
    source text NOT NULL DEFAULT 'dx-helpdesk' CHECK (length(btrim(source)) > 0),
    created_by text NOT NULL CHECK (length(btrim(created_by)) > 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    deleted_at timestamptz
);

-- Append-only from the Data API's perspective. Record field edits, transitions,
-- attachment changes and deletion here; do not replace Flowable's process history.
CREATE TABLE ticket_events (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ticket_id uuid NOT NULL REFERENCES tickets(id),
    action text NOT NULL CHECK (length(btrim(action)) > 0),
    from_status text CHECK (from_status IN (
        'DRAFT', 'SUBMITTED', 'ASSIGNED', 'IN_PROGRESS',
        'RESOLVED', 'CLOSED', 'REJECTED'
    )),
    to_status text CHECK (to_status IN (
        'DRAFT', 'SUBMITTED', 'ASSIGNED', 'IN_PROGRESS',
        'RESOLVED', 'CLOSED', 'REJECTED'
    )),
    actor_sub text NOT NULL CHECK (length(btrim(actor_sub)) > 0),
    source text NOT NULL CHECK (length(btrim(source)) > 0),
    details jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(details) = 'object'),
    occurred_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX tickets_active_created_idx ON tickets (created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX tickets_active_owner_idx ON tickets (created_by, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX tickets_active_assignee_idx ON tickets (assigned_to, created_at DESC)
    WHERE deleted_at IS NULL AND assigned_to IS NOT NULL;
CREATE INDEX tickets_active_status_idx ON tickets (status, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX tickets_active_category_idx ON tickets (category, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX ticket_attachments_active_ticket_idx ON ticket_attachments (ticket_id, created_at)
    WHERE deleted_at IS NULL;
CREATE INDEX ticket_events_ticket_time_idx ON ticket_events (ticket_id, occurred_at, id);

CREATE FUNCTION set_ticket_updated_at() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER tickets_updated_at
    BEFORE UPDATE ON tickets
    FOR EACH ROW EXECUTE FUNCTION set_ticket_updated_at();

COMMIT;

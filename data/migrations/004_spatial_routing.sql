-- SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
-- SPDX-License-Identifier: Apache-2.0

BEGIN;
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS latitude double precision
    CHECK (latitude BETWEEN -90 AND 90);
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS longitude double precision
    CHECK (longitude BETWEEN -180 AND 180);
CREATE TABLE IF NOT EXISTS campus_areas (
    code text PRIMARY KEY CHECK (code IN ('CS1', 'CS2', 'CS3')),
    boundary geometry(Polygon, 4326) NOT NULL
);
CREATE INDEX IF NOT EXISTS campus_areas_boundary_gix ON campus_areas USING gist (boundary);
CREATE TABLE IF NOT EXISTS location_points (
    location_id integer PRIMARY KEY REFERENCES site_locations(location_id),
    point geometry(Point, 4326) NOT NULL
);
-- Source: data/samples/campuses.json, team-estimated polygons (Apache-2.0).
INSERT INTO campus_areas (code, boundary) VALUES
('CS1', ST_GeomFromText('POLYGON((105.73365 21.05315,105.73682 21.05282,105.73715 21.05452,105.73421 21.05495,105.73365 21.05315))',4326)),
('CS2', ST_GeomFromText('POLYGON((105.71802 21.0655,105.7212 21.0653,105.7215 21.0674,105.7182 21.0676,105.71802 21.0655))',4326)),
('CS3', ST_GeomFromText('POLYGON((105.9168 20.5472,105.9209 20.5471,105.9211 20.5501,105.917 20.5502,105.9168 20.5472))',4326))
ON CONFLICT (code) DO UPDATE SET boundary = EXCLUDED.boundary;
-- The sample contains no building/room coordinates. Use each campus interior
-- as an approximate point for its Snipe-IT location IDs until surveyed points exist.
INSERT INTO location_points (location_id, point)
SELECT l.location_id, ST_PointOnSurface(c.boundary)
FROM site_locations l JOIN campus_areas c ON c.code = l.co_so
ON CONFLICT (location_id) DO UPDATE SET point = EXCLUDED.point;
COMMIT;

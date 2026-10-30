# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

"""Initialize dxdata or apply outstanding migrations before serving requests."""

import os
from pathlib import Path

import pg8000.dbapi

POSTGIS_MISSING = (
    "Data API cần PostGIS 3.x trên database dxdata (định tuyến theo cơ sở, #79). "
    "Cài PostGIS 3 cho PostgreSQL, rồi chạy bằng tài khoản superuser: "
    "psql -d dxdata -c 'CREATE EXTENSION postgis'. Lỗi gốc: {}")


def ensure_postgis(cur):
    """Require the extension installed by the PostgreSQL superuser before migration."""
    try:
        # Even IF NOT EXISTS checks CREATE privileges; dxdata is not a superuser.
        cur.execute("SELECT extversion FROM pg_extension WHERE extname = 'postgis'")
        if cur.fetchone() is None:
            raise SystemExit(POSTGIS_MISSING.format("extension chưa được bật trên dxdata"))
        cur.execute("SELECT postgis_lib_version()")
        version = cur.fetchone()[0]
    except pg8000.dbapi.DatabaseError as exc:
        message = exc.args[0].get("M", exc) if exc.args and isinstance(exc.args[0], dict) else exc
        raise SystemExit(POSTGIS_MISSING.format(message)) from None
    if not str(version).startswith("3."):
        raise SystemExit(POSTGIS_MISSING.format(f"đang có PostGIS {version}"))


def main():
    db = pg8000.dbapi.connect(host=os.getenv("DATA_DB_HOST", "postgres"), port=5432,
                              database="dxdata", user="dxdata",
                              password=os.environ["DATA_DB_PASSWORD"])
    db.autocommit = True
    try:
        cur = db.cursor()
        cur.execute("SELECT pg_advisory_lock(202620)")
        ensure_postgis(cur)
        cur.execute("SELECT to_regclass('public.tickets')")
        existing = cur.fetchone()[0] is not None
        if not existing:
            cur.execute((Path(__file__).parent / "schema.sql").read_text())
        cur.execute("""CREATE TABLE IF NOT EXISTS schema_migrations (
            version integer PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())""")
        if not existing:
            cur.execute("INSERT INTO schema_migrations(version) VALUES (1),(2),(3) ON CONFLICT DO NOTHING")
        for version, script in ((1, "001_data_api.sql"), (2, "002_provenance.sql"),
                                (3, "003_ticket_code.sql"), (4, "004_spatial_routing.sql")):
            cur.execute("SELECT 1 FROM schema_migrations WHERE version = %s", (version,))
            if cur.fetchone() is None:
                cur.execute((Path(__file__).parent / "migrations" / script).read_text())
                cur.execute("INSERT INTO schema_migrations(version) VALUES (%s)", (version,))
    finally:
        db.close()


if __name__ == "__main__":
    main()

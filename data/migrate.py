# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

"""Initialize dxdata or apply outstanding migrations before serving requests."""

import os
from pathlib import Path

import pg8000.dbapi


def main():
    db = pg8000.dbapi.connect(host=os.getenv("DATA_DB_HOST", "postgres"), port=5432,
                              database="dxdata", user="dxdata",
                              password=os.environ["DATA_DB_PASSWORD"])
    db.autocommit = True
    try:
        cur = db.cursor()
        cur.execute("SELECT pg_advisory_lock(202620)")
        cur.execute("SELECT to_regclass('public.tickets')")
        existing = cur.fetchone()[0] is not None
        if not existing:
            cur.execute((Path(__file__).parent / "schema.sql").read_text())
        cur.execute("""CREATE TABLE IF NOT EXISTS schema_migrations (
            version integer PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())""")
        if not existing:
            cur.execute("INSERT INTO schema_migrations(version) VALUES (1),(2),(3) ON CONFLICT DO NOTHING")
        else:
            for version, script in ((1, "001_data_api.sql"), (2, "002_provenance.sql"),
                                    (3, "003_ticket_code.sql")):
                cur.execute("SELECT 1 FROM schema_migrations WHERE version = %s", (version,))
                if cur.fetchone() is None:
                    cur.execute((Path(__file__).parent / "migrations" / script).read_text())
                    cur.execute("INSERT INTO schema_migrations(version) VALUES (%s)", (version,))
    finally:
        db.close()


if __name__ == "__main__":
    main()

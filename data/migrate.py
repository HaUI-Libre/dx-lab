# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

"""Initialize dxdata or upgrade the issue #16 schema before serving requests."""

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
        script = "migrations/001_data_api.sql" if cur.fetchone()[0] else "schema.sql"
        cur.execute((Path(__file__).parent / script).read_text())
    finally:
        db.close()


if __name__ == "__main__":
    main()

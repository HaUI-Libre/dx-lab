# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

"""Existing volumes can start Data API without extension creation privileges."""

import pytest

from data.migrate import ensure_postgis


class Cursor:
    def __init__(self, rows):
        self.rows = iter(rows)
        self.queries = []

    def execute(self, sql):
        self.queries.append(sql)

    def fetchone(self):
        return next(self.rows)


def test_existing_postgis_needs_no_create_privilege():
    cursor = Cursor([("3.6.4",), ("3.6.4",)])
    ensure_postgis(cursor)
    assert all("CREATE EXTENSION" not in query for query in cursor.queries)


def test_missing_postgis_stops_before_schema_changes():
    cursor = Cursor([None])
    with pytest.raises(SystemExit, match="extension chưa được bật"):
        ensure_postgis(cursor)
    assert len(cursor.queries) == 1

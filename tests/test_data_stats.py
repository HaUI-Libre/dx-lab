# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

"""Issue #22: dashboard statistics are scoped by the token's site, not the client."""

import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
import app as data_api  # noqa: E402


def caller(role="ROLE_LAB_MANAGER", site="CS1"):
    return {"roles": {role}, "co_so": site, "sub": "user", "username": "user",
            "token": "signed-user-token"}


@pytest.fixture
def queries(monkeypatch):
    """Record each SQL statement with its parameters and answer with canned rows."""
    seen = []
    groups = {
        "status": [{"key": "SUBMITTED", "n": 2}, {"key": "CLOSED", "n": 3}],
        "category": [{"key": "HARDWARE", "n": 4}, {"key": None, "n": 1}],
        "co_so": [{"key": "CS1", "n": 5}],
    }

    @contextmanager
    def fake_database():
        yield object()

    def many(_db, sql, params=()):
        seen.append((sql, list(params)))
        field = sql.split("SELECT t.", 1)[1].split(" ", 1)[0]
        return groups[field]

    def one(_db, sql, params=()):
        seen.append((sql, list(params)))
        if "ticket_events" in sql:
            return {"n": 2}
        return {"hours": Decimal("7.456"), "overdue": 1}

    monkeypatch.setattr(data_api, "database", fake_database)
    monkeypatch.setattr(data_api, "many", many)
    monkeypatch.setattr(data_api, "one", one)
    return seen


def stats(user, co_so=None, from_=None, to=None):
    return data_api.ticket_stats(co_so=co_so, from_=from_, to=to, user=user)


def test_manager_gets_own_site_from_token(queries):
    result = stats(caller())
    assert result == {
        "total": 5, "by_status": {"SUBMITTED": 2, "CLOSED": 3},
        "by_category": {"HARDWARE": 4}, "by_co_so": {"CS1": 5},
        "average_resolution_hours": 7.46, "overdue_count": 1, "reopen_count": 2}
    for sql, params in queries:
        assert "t.co_so = %s" in sql and params == ["CS1"]
        assert "t.deleted_at IS NULL" in sql and "t.status <> 'DRAFT'" in sql


def test_manager_cannot_ask_for_another_site(queries):
    with pytest.raises(data_api.HTTPException) as error:
        stats(caller(), co_so="CS2")
    assert error.value.status_code == 403
    assert not queries


def test_manager_without_site_is_denied(queries):
    with pytest.raises(data_api.HTTPException) as error:
        stats(caller(site=None))
    assert error.value.status_code == 403


@pytest.mark.parametrize("role", ["ROLE_STUDENT", "ROLE_TECHNICIAN"])
def test_other_roles_are_denied(queries, role):
    with pytest.raises(data_api.HTTPException) as error:
        stats(caller(role))
    assert error.value.status_code == 403
    assert not queries


def test_admin_sees_all_sites_or_one(queries):
    stats(caller("ROLE_ADMIN", None))
    assert all("t.co_so = %s" not in sql and params == [] for sql, params in queries)
    queries.clear()
    stats(caller("ROLE_ADMIN", None), co_so="CS3")
    assert all(params == ["CS3"] for _, params in queries)


def test_period_filter_and_order(queries):
    start = datetime(2026, 10, 1, tzinfo=timezone.utc)
    end = datetime(2026, 11, 1, tzinfo=timezone.utc)
    stats(caller("ROLE_ADMIN", None), from_=start, to=end)
    sql, params = queries[0]
    assert "t.created_at >= %s" in sql and "t.created_at < %s" in sql
    assert params == [start, end]
    with pytest.raises(data_api.HTTPException) as error:
        stats(caller("ROLE_ADMIN", None), from_=end, to=start)
    assert error.value.status_code == 422


def test_no_resolved_ticket_gives_null_average(queries, monkeypatch):
    monkeypatch.setattr(data_api, "one", lambda _db, sql, params=():
                        {"n": 0} if "ticket_events" in sql else {"hours": None, "overdue": 0})
    assert stats(caller())["average_resolution_hours"] is None

# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

"""Security and workflow boundary checks for issue #20."""

import sys
import json
import re
import time
from types import SimpleNamespace
from contextlib import contextmanager
from pathlib import Path
from uuid import UUID

import pytest
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
import app as data_api  # noqa: E402


TICKET = "a1111111-1111-4111-8111-111111111101"


def identity(role="ROLE_LAB_MANAGER", site="CS1", sub="manager"):
    return {"sub": sub, "username": sub, "co_so": site,
            "roles": {role}, "token": "test-token"}


@contextmanager
def fake_database():
    yield object()


@pytest.fixture
def db(monkeypatch):
    monkeypatch.setattr(data_api, "database", fake_database)


def test_manager_cannot_read_another_site(monkeypatch, db):
    row = {"id": TICKET, "status": "SUBMITTED", "created_by": "manager",
           "co_so": "CS2", "assigned_to": None}
    monkeypatch.setattr(data_api, "one", lambda _db, _sql, _params: row)
    with pytest.raises(data_api.HTTPException) as error:
        data_api.get_ticket(UUID(TICKET), user=identity())
    assert error.value.status_code == 404


def test_list_filters_by_site_from_token(monkeypatch, db):
    calls = []

    def one(_db, sql, params):
        calls.append((sql, params))
        return {"count": 0}

    def many(_db, sql, params):
        calls.append((sql, params))
        return []

    monkeypatch.setattr(data_api, "one", one)
    monkeypatch.setattr(data_api, "many", many)
    result = data_api.list_tickets(status=data_api.Status.SUBMITTED, category=None,
                                   priority=None, q="printer", page=1, page_size=20,
                                   user=identity())
    assert result["total"] == 0
    assert all("co_so = %s" in sql for sql, _ in calls)
    assert all("CS1" in params and "SUBMITTED" in params for _, params in calls)


def test_submit_uses_server_site_mapping(monkeypatch, db):
    row = {"id": TICKET, "status": "DRAFT", "created_by": "student", "co_so": None,
           "category": "HARDWARE", "priority": "HIGH", "asset_id": 42, "location_id": 12}
    calls = []
    monkeypatch.setattr(data_api, "asset_location", lambda asset_id, token: 6)

    def one(_db, sql, params):
        if "SELECT * FROM tickets" in sql:
            return row
        if "SELECT co_so FROM site_locations" in sql:
            assert params == (6,)
            return {"co_so": "CS1"}
        if "UPDATE tickets" in sql:
            assert params[1] == 6
            return {**row, "status": "SUBMITTED", "co_so": "CS1"}
        raise AssertionError(sql)

    monkeypatch.setattr(data_api, "one", one)
    monkeypatch.setattr(data_api, "event", lambda *args: None)
    monkeypatch.setattr(data_api, "flowable", lambda *args, **kwargs: calls.append(args) or {"id": "instance-1"})
    response = data_api.transition(UUID(TICKET), data_api.Action.submit, data_api.ActionBody(),
                                   user=identity("ROLE_STUDENT", None, "student"))
    assert response["co_so"] == "CS1"
    sent = calls[0][3]
    assert {v["name"]: v["value"] for v in sent["variables"]}["co_so"] == "CS1"


def test_reject_requires_reason_before_flowable(monkeypatch, db):
    row = {"id": TICKET, "status": "SUBMITTED", "created_by": "student", "co_so": "CS1",
           "assigned_to": None, "workflow_instance_id": "process-1"}
    monkeypatch.setattr(data_api, "one", lambda _db, _sql, _params: row)
    monkeypatch.setattr(data_api, "current_task", lambda *_: {"id": "task-1"})
    monkeypatch.setattr(data_api, "flowable", lambda *_args, **_kwargs: pytest.fail("Flowable was called"))
    with pytest.raises(data_api.HTTPException) as error:
        data_api.transition(UUID(TICKET), data_api.Action.reject,
                            data_api.ActionBody(reason="   "), user=identity())
    assert error.value.status_code == 422


def test_assign_rejects_technician_from_other_site(monkeypatch, db):
    row = {"id": TICKET, "status": "SUBMITTED", "created_by": "student", "co_so": "CS1",
           "assigned_to": None, "workflow_instance_id": "process-1"}
    monkeypatch.setattr(data_api, "one", lambda _db, _sql, _params: row)
    monkeypatch.setattr(data_api, "current_task", lambda *_: {"id": "task-1"})
    monkeypatch.setattr(data_api, "technician", lambda sub, site: (_ for _ in ()).throw(
        data_api.HTTPException(422, "wrong site")))
    monkeypatch.setattr(data_api, "flowable", lambda *_args, **_kwargs: pytest.fail("Flowable was called"))
    with pytest.raises(data_api.HTTPException) as error:
        data_api.transition(UUID(TICKET), data_api.Action.assign,
                            data_api.ActionBody(technician_sub="tech-cs2"), user=identity())
    assert error.value.status_code == 422


def test_unsigned_or_missing_token_is_rejected():
    with pytest.raises(data_api.HTTPException) as missing:
        data_api.caller(None)
    assert missing.value.status_code == 401


def test_access_token_signature_and_issuer(monkeypatch):
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setattr(data_api, "JWKS", SimpleNamespace(
        get_signing_key_from_jwt=lambda _token: SimpleNamespace(key=private.public_key())))
    claims = {"iss": data_api.ISSUER, "azp": "dxlab-app", "typ": "Bearer",
              "sub": "student", "preferred_username": "sinhvien",
              "realm_access": {"roles": ["ROLE_STUDENT"]}, "exp": int(time.time()) + 60}
    token = jwt.encode(claims, private, algorithm="RS256")
    assert data_api.caller(f"Bearer {token}")["sub"] == "student"
    wrong = jwt.encode({**claims, "iss": "http://wrong-issuer"}, private, algorithm="RS256")
    with pytest.raises(data_api.HTTPException) as error:
        data_api.caller(f"Bearer {wrong}")
    assert error.value.status_code == 401


def test_site_mapping_matches_snipeit_sample():
    root = Path(__file__).resolve().parents[1]
    locations = json.loads((root / "data/samples/snipeit_seed.json").read_text())["locations"]
    expected = {(item["id"], item["code"], item["campus_code"]) for item in locations}
    for path in (root / "data/schema.sql", root / "data/migrations/001_data_api.sql"):
        actual = {(int(number), code, site) for number, code, site in
                  re.findall(r"\((\d+),'([^']+)','(CS[123])'\)", path.read_text())}
        assert actual == expected

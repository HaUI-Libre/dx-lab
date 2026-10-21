# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

"""Issue #21: provenance visibility, reasons and asset update outcomes."""

import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
import app as data_api  # noqa: E402


TICKET_ID = UUID("a1111111-1111-4111-8111-111111111101")


def caller(role="ROLE_LAB_MANAGER", site="CS1", sub="manager"):
    return {"roles": {role}, "co_so": site, "sub": sub,
            "username": sub, "token": "signed-user-token"}


@contextmanager
def fake_database():
    yield object()


@pytest.fixture
def db(monkeypatch):
    monkeypatch.setattr(data_api, "database", fake_database)


def test_provenance_counts_reopens_and_includes_deleted_draft(monkeypatch, db):
    now = datetime.now(timezone.utc)
    ticket = {"id": TICKET_ID, "status": "DRAFT", "created_by": "student",
              "co_so": None, "source": "dx-helpdesk", "created_at": now,
              "updated_at": now, "deleted_at": now}
    history = [{"action": "CREATE_DRAFT"}, {"action": "REOPEN"},
               {"action": "REOPEN"}, {"action": "ASSET_STATUS_UPDATE_FAILED"}]
    monkeypatch.setattr(data_api, "one", lambda *_: ticket)
    monkeypatch.setattr(data_api, "many", lambda *_: history)
    result = data_api.get_ticket_provenance(TICKET_ID,
                                            user=caller("ROLE_STUDENT", None, "student"))
    assert result["reopen_count"] == 2
    assert result["deleted_at"] == now
    assert result["events"] == history


def test_provenance_denies_other_site(monkeypatch, db):
    monkeypatch.setattr(data_api, "one", lambda *_: {
        "id": TICKET_ID, "status": "SUBMITTED", "created_by": "student",
        "co_so": "CS2", "source": "dx-helpdesk"})
    with pytest.raises(data_api.HTTPException) as error:
        data_api.get_ticket_provenance(TICKET_ID, user=caller())
    assert error.value.status_code == 404


def test_events_require_ticket_visibility(monkeypatch, db):
    ticket = {"id": TICKET_ID, "status": "SUBMITTED", "created_by": "student",
              "co_so": "CS2", "assigned_to": None}
    monkeypatch.setattr(data_api, "one", lambda *_: ticket)
    monkeypatch.setattr(data_api, "many", lambda *_: pytest.fail("History leaked"))
    with pytest.raises(data_api.HTTPException) as error:
        data_api.list_ticket_events(TICKET_ID, user=caller())
    assert error.value.status_code == 404


def test_event_source_accepts_external_values(monkeypatch):
    inserted = []
    monkeypatch.setattr(data_api, "execute", lambda _db, sql, params: inserted.append((sql, params)))
    data_api.event(object(), TICKET_ID, "ASSET_STATUS_UPDATE_SUCCEEDED", caller(),
                   "CLOSED", "CLOSED", {"outcome": "SUCCEEDED"},
                   source=data_api.Source.SNIPE_IT)
    data_api.event(object(), TICKET_ID, "STATUS_SYNC", caller(), "CLOSED", "CLOSED",
                   source=data_api.Source.NATS)
    assert [params[3] for _, params in inserted] == ["snipe-it", "nats"]


@pytest.mark.parametrize("action,status,target", [
    (data_api.Action.reject, "SUBMITTED", "REJECTED"),
    (data_api.Action.reopen, "RESOLVED", "IN_PROGRESS"),
])
def test_reject_and_reopen_keep_reason(monkeypatch, db, action, status, target):
    row = {"id": TICKET_ID, "status": status, "created_by": "student",
           "co_so": "CS1", "assigned_to": "tech", "workflow_instance_id": "process-1"}
    events = []
    monkeypatch.setattr(data_api, "one", lambda _db, sql, _params: (
        {**row, "status": target} if "UPDATE tickets" in sql else row))
    monkeypatch.setattr(data_api, "current_task", lambda *_: {"id": "task-1"})
    monkeypatch.setattr(data_api, "flowable", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(data_api, "event", lambda *args, **_kwargs: events.append(args))
    data_api.transition(TICKET_ID, action, data_api.ActionBody(reason="  Cần xử lý lại  "),
                        user=caller())
    assert events[0][2] == action.value.upper()
    assert events[0][6] == {"reason": "Cần xử lý lại"}


def test_asset_update_records_success_and_failure(monkeypatch, db):
    url = "http://apisix:9080/api/assets/internal/status"
    monkeypatch.setenv("DATA_ASSET_STATUS_URL", url)
    monkeypatch.setenv("DATA_ASSET_KEY", "test-secret")
    ticket = {"id": TICKET_ID, "asset_id": 42, "status": "CLOSED",
              "resolution_summary": "Đã sửa"}
    events = []
    monkeypatch.setattr(data_api, "event", lambda *args, **kwargs: events.append((args, kwargs)))
    monkeypatch.setattr(data_api.httpx, "post", lambda *_args, **_kwargs: httpx.Response(
        204, request=httpx.Request("POST", url)))
    data_api.record_asset_status_update(caller(), ticket)
    assert events[-1][0][2] == "ASSET_STATUS_UPDATE_SUCCEEDED"
    assert events[-1][1]["source"] == data_api.Source.SNIPE_IT
    assert events[-1][0][6]["http_status"] == 204

    monkeypatch.setattr(data_api.httpx, "post", lambda *_args, **_kwargs: httpx.Response(
        503, request=httpx.Request("POST", url)))
    data_api.record_asset_status_update(caller(), ticket)
    assert events[-1][0][2] == "ASSET_STATUS_UPDATE_FAILED"
    assert events[-1][0][6]["reason"] == "http_error"
    assert events[-1][1]["source"] == data_api.Source.DX_HELPDESK


def test_bad_asset_url_is_logged_without_raising(monkeypatch, db):
    monkeypatch.setenv("DATA_ASSET_STATUS_URL", "://bad-url")
    monkeypatch.setenv("DATA_ASSET_KEY", "test-secret")
    events = []
    monkeypatch.setattr(data_api, "event", lambda *args, **_kwargs: events.append(args))
    data_api.record_asset_status_update(caller(), {
        "id": TICKET_ID, "asset_id": 42, "status": "IN_PROGRESS"})
    assert events[-1][2] == "ASSET_STATUS_UPDATE_FAILED"
    assert events[-1][6]["reason"] == "transport_error"


def test_missing_integration_is_audited_without_http_call(monkeypatch, db):
    monkeypatch.delenv("DATA_ASSET_STATUS_URL", raising=False)
    monkeypatch.setattr(data_api.httpx, "post", lambda *_args, **_kwargs: pytest.fail("HTTP called"))
    events = []
    monkeypatch.setattr(data_api, "event", lambda *args, **_kwargs: events.append(args))
    data_api.record_asset_status_update(caller(), {
        "id": TICKET_ID, "asset_id": 42, "status": "IN_PROGRESS"})
    assert events[-1][2] == "ASSET_STATUS_UPDATE_FAILED"
    assert events[-1][6]["reason"] == "integration_not_configured"


def test_start_records_pending_before_dispatch(monkeypatch, db):
    row = {"id": TICKET_ID, "status": "ASSIGNED", "created_by": "student",
           "co_so": "CS1", "assigned_to": "tech", "workflow_instance_id": "process-1",
           "asset_id": 42}
    ordered = []
    monkeypatch.setattr(data_api, "one", lambda _db, sql, _params: (
        {**row, "status": "IN_PROGRESS"} if "UPDATE tickets" in sql else row))
    monkeypatch.setattr(data_api, "current_task", lambda *_: {
        "id": "task-1", "assignee": "tech"})
    monkeypatch.setattr(data_api, "flowable", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(data_api, "event", lambda _db, _id, action, *_args, **_kwargs:
                        ordered.append(action))
    monkeypatch.setattr(data_api, "record_asset_status_update", lambda *_:
                        ordered.append("dispatch"))
    updated = data_api.transition(TICKET_ID, data_api.Action.start, data_api.ActionBody(),
                                  user=caller("ROLE_TECHNICIAN", "CS1", "tech"))
    assert updated["status"] == "IN_PROGRESS"
    assert ordered == ["START_PROGRESS", "ASSET_STATUS_UPDATE_PENDING", "dispatch"]


def test_rating_change_has_before_and_after(monkeypatch, db):
    row = {"id": TICKET_ID, "status": "CLOSED", "created_by": "student",
           "co_so": "CS1", "satisfaction_rating": 3}
    events = []
    monkeypatch.setattr(data_api, "one", lambda _db, sql, _params: (
        {**row, "satisfaction_rating": 5} if "UPDATE tickets" in sql else row))
    monkeypatch.setattr(data_api, "event", lambda *args, **_kwargs: events.append(args))
    result = data_api.rate_ticket(TICKET_ID, data_api.RatingBody(rating=5),
                                  user=caller("ROLE_STUDENT", None, "student"))
    assert result["satisfaction_rating"] == 5
    assert events[0][6] == {"rating": {"before": 3, "after": 5}}

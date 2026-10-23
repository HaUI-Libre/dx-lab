# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

"""Issue #72: Snipe-IT adapter, status restoration and durable retry."""

import importlib.util
import json
import sys
from pathlib import Path
from uuid import UUID

import httpx
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "integration/assets"))
from adapter import AssetError, SnipeIT  # noqa: E402

spec = importlib.util.spec_from_file_location("asset_sync_app", ROOT / "integration/assets/app.py")
asset_sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asset_sync)

TICKET = UUID("a1111111-1111-4111-8111-111111111101")


def test_snipe_adapter_resolves_exact_user_tag_and_room(tmp_path, monkeypatch):
    token_file = tmp_path / "token"
    token_file.write_text("sample-token\n")
    monkeypatch.setenv("SNIPEIT_TOKEN_FILE", str(token_file))
    calls = []

    def reply(request):
        calls.append((request.method, request.url.path, request.headers.get("Authorization")))
        path = request.url.path
        if path.endswith("/users"):
            result = {"rows": [{"id": 1, "username": "sinhvien_cs2"},
                               {"id": 2, "username": "sinhvien"}]}
        elif path.endswith("/users/2/assets") or path.endswith("/locations/12/assets"):
            result = {"rows": [{"id": 4, "asset_tag": "HAUI-PC-0004", "name": "PC",
                                "location": {"id": 12, "name": "PM201"}}]}
        elif path.endswith("/locations/12"):
            result = {"id": 12, "parent": {"id": 10}}
        elif path.endswith("/locations/10"):
            result = {"id": 10, "parent": {"id": 9}}
        elif path.endswith("/hardware/bytag/HAUI-PC-0004"):
            result = {"id": 4, "asset_tag": "HAUI-PC-0004", "location": {"id": 12, "name": "PM201"}}
        else:
            raise AssertionError(path)
        return httpx.Response(200, json=result)

    api = SnipeIT(httpx.Client(transport=httpx.MockTransport(reply)))
    mine = api.assets_for_username("sinhvien")
    assert mine == [{"id": 4, "asset_tag": "HAUI-PC-0004", "name": "PC",
                     "location_id": 12, "location": "PM201", "co_so": "CS2"}]
    assert api.by_tag("HAUI-PC-0004")["co_so"] == "CS2"
    assert api.by_location(12)[0]["id"] == 4
    assert all(token == "Bearer sample-token" for _, _, token in calls)


def test_snipe_patch_checks_application_response(tmp_path, monkeypatch):
    token_file = tmp_path / "token"
    token_file.write_text("sample-token")
    monkeypatch.setenv("SNIPEIT_TOKEN_FILE", str(token_file))
    bodies = []

    def reply(request):
        bodies.append(json.loads(request.content))
        return httpx.Response(200, json={"status": "success"})

    api = SnipeIT(httpx.Client(transport=httpx.MockTransport(reply)))
    api.set_status(4, 7, notes="Ticket repaired")
    assert bodies == [{"status_id": 7, "notes": "Ticket repaired"}]

    api.client = httpx.Client(transport=httpx.MockTransport(
        lambda _request: httpx.Response(200, json={"status": "error"})))
    with pytest.raises(AssetError):
        api.set_status(4, 7)


class FakeAdapter:
    def __init__(self):
        self.status = 2
        self.notes = "Ghi chú cũ"
        self.fail_once = False
        self.changes = []

    def asset(self, _id):
        return {"status_label": {"id": self.status}, "notes": self.notes}

    def repair_status_id(self):
        return 7

    def set_status(self, _id, status_id, notes=None):
        if self.fail_once:
            self.fail_once = False
            raise AssetError("Snipe-IT unavailable")
        self.status = status_id
        if notes is not None:
            self.notes = notes
        self.changes.append((status_id, notes))


def test_start_close_restores_original_status_and_records_notes(tmp_path, monkeypatch):
    fake = FakeAdapter()
    monkeypatch.setattr(asset_sync, "store", asset_sync.Store(tmp_path / "updates.sqlite3"))
    monkeypatch.setattr(asset_sync, "adapter", lambda: fake)
    start = asset_sync.StatusUpdate(ticket_id=TICKET, asset_id=4, to_status="IN_PROGRESS")
    close = asset_sync.StatusUpdate(ticket_id=TICKET, asset_id=4, to_status="CLOSED",
                                    resolution_summary="Thay bộ nguồn")
    assert asset_sync.apply_update(start)["result"] == "SUCCEEDED"
    assert fake.status == 7
    assert asset_sync.apply_update(close)["result"] == "SUCCEEDED"
    assert fake.status == 2
    assert fake.notes.startswith("Ghi chú cũ\nTicket")
    assert "Thay bộ nguồn" in fake.notes
    assert asset_sync.store.get(TICKET)["original_status_id"] == 2
    asset_sync.apply_update(close)
    assert fake.notes.count("Thay bộ nguồn") == 1


def test_failure_is_durable_and_retryable(tmp_path, monkeypatch):
    fake = FakeAdapter()
    fake.fail_once = True
    path = tmp_path / "updates.sqlite3"
    monkeypatch.setattr(asset_sync, "store", asset_sync.Store(path))
    monkeypatch.setattr(asset_sync, "adapter", lambda: fake)
    update = asset_sync.StatusUpdate(ticket_id=TICKET, asset_id=4, to_status="IN_PROGRESS")
    with pytest.raises(asset_sync.HTTPException) as error:
        asset_sync.apply_update(update)
    assert error.value.status_code == 503
    assert asset_sync.Store(path).get(TICKET)["result"] == "FAILED"
    assert asset_sync.retry_ticket(TICKET)["result"] == "SUCCEEDED"
    assert asset_sync.Store(path).get(TICKET)["attempts"] == 2
    assert fake.status == 7


def test_initial_read_failure_is_queued(tmp_path, monkeypatch):
    fake = FakeAdapter()
    original = fake.asset
    calls = 0

    def read(asset_id):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise AssetError("Snipe-IT offline")
        return original(asset_id)

    fake.asset = read
    monkeypatch.setattr(asset_sync, "store", asset_sync.Store(tmp_path / "updates.sqlite3"))
    monkeypatch.setattr(asset_sync, "adapter", lambda: fake)
    update = asset_sync.StatusUpdate(ticket_id=TICKET, asset_id=4, to_status="IN_PROGRESS")
    with pytest.raises(asset_sync.HTTPException):
        asset_sync.apply_update(update)
    assert asset_sync.store.get(TICKET)["result"] == "FAILED"
    assert asset_sync.store.get(TICKET)["original_status_id"] is None
    assert asset_sync.retry_ticket(TICKET)["result"] == "SUCCEEDED"
    assert asset_sync.store.get(TICKET)["original_status_id"] == 2


def test_routes_use_verified_identity_and_internal_key(tmp_path, monkeypatch):
    fake = FakeAdapter()
    fake.assets_for_username = lambda name: [{"id": 4, "asset_tag": name}]
    monkeypatch.setattr(asset_sync, "store", asset_sync.Store(tmp_path / "updates.sqlite3"))
    monkeypatch.setattr(asset_sync, "adapter", lambda: fake)
    monkeypatch.setenv("DATA_ASSET_KEY", "test-internal-key")
    assert asset_sync.my_assets(user={"preferred_username": "sinhvien"}) == [
        {"id": 4, "asset_tag": "sinhvien"}]
    with pytest.raises(asset_sync.HTTPException) as error:
        asset_sync.internal_key("wrong-key")
    assert error.value.status_code == 403
    asset_sync.internal_key("test-internal-key")
    payload = asset_sync.StatusUpdate(ticket_id=TICKET, asset_id=4, to_status="IN_PROGRESS")
    assert asset_sync.update_status(payload)["result"] == "SUCCEEDED"

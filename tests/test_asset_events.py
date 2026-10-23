# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

"""Issue #77: status_changed events between Data API and asset-sync."""

import asyncio
import importlib.util
import json
import sys
from pathlib import Path

from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "integration/assets"))
spec = importlib.util.spec_from_file_location("asset_sync_events", ROOT / "integration/assets/app.py")
asset_sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asset_sync)

sys.path.insert(0, str(ROOT / "data"))
import app as data_api  # noqa: E402

TICKET = "a1111111-1111-4111-8111-111111111101"


class Message:
    def __init__(self, payload):
        self.data = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.calls = []

    async def ack(self):
        self.calls.append("ack")

    async def nak(self, delay=None):
        self.calls.append("nak")

    async def term(self):
        self.calls.append("term")


def run(payload, monkeypatch, outcome=None):
    seen = []

    def apply(update):
        seen.append(update)
        if outcome:
            raise outcome

    monkeypatch.setattr(asset_sync, "apply_update", apply)
    msg = Message(payload)
    asyncio.run(asset_sync.handle_event(msg))
    return msg.calls, seen


def event(to_status, asset_id=4):
    return {"ticket_id": TICKET, "to_status": to_status, "asset_id": asset_id,
            "resolution_summary": "Thay nguồn"}


def test_only_repair_and_close_reach_snipe(monkeypatch):
    calls, seen = run(event("ASSIGNED"), monkeypatch)
    assert calls == ["ack"] and seen == []
    calls, seen = run(event("IN_PROGRESS", asset_id=None), monkeypatch)
    assert calls == ["ack"] and seen == []
    calls, seen = run(event("CLOSED"), monkeypatch)
    assert calls == ["ack"] and seen[0].to_status == "CLOSED" and seen[0].asset_id == 4


def test_failed_snipe_call_is_acked_because_store_retries(monkeypatch):
    calls, _ = run(event("IN_PROGRESS"), monkeypatch, HTTPException(503, "queued for retry"))
    assert calls == ["ack"]


def test_unexpected_error_is_redelivered_and_bad_payload_dropped(monkeypatch):
    calls, _ = run(event("IN_PROGRESS"), monkeypatch, RuntimeError("disk full"))
    assert calls == ["nak"]
    calls, seen = run(b"not json", monkeypatch)
    assert calls == ["term"] and seen == []


def test_data_api_falls_back_when_bus_is_unavailable(monkeypatch):
    ticket = {"id": TICKET, "status": "CLOSED", "asset_id": 4, "co_so": "CS1",
              "resolution_summary": "x", "updated_at": "2026-10-23T10:00:00+07:00"}
    user = {"sub": "manager"}
    monkeypatch.setattr(data_api, "NATS_URL", "")
    assert data_api.publish_status_changed(user, "RESOLVED", ticket, "close") is False

    async def broken(payload, msg_id):
        raise OSError("nats unreachable")

    monkeypatch.setattr(data_api, "NATS_URL", "nats://nats:4222")
    monkeypatch.setattr(data_api, "_bus_down_until", 0.0)
    monkeypatch.setattr(data_api, "_publish", broken)
    assert data_api.publish_status_changed(user, "RESOLVED", ticket, "close") is False
    # The next call skips the bus instead of waiting again
    assert data_api._bus_down_until > 0

    async def slow(payload, msg_id):
        await asyncio.sleep(10)

    monkeypatch.setattr(data_api, "_bus_down_until", 0.0)
    monkeypatch.setattr(data_api, "_publish", slow)
    started = data_api.time.monotonic()
    assert data_api.publish_status_changed(user, "RESOLVED", ticket, "close") is False
    assert data_api.time.monotonic() - started < 5

    monkeypatch.setattr(data_api, "_bus_down_until", 0.0)
    sent = []

    async def ok(payload, msg_id):
        sent.append((payload, msg_id))

    monkeypatch.setattr(data_api, "_publish", ok)
    assert data_api.publish_status_changed(user, "RESOLVED", ticket, "close") is True
    payload, msg_id = sent[0]
    assert payload["to_status"] == "CLOSED" and payload["from_status"] == "RESOLVED"
    assert msg_id == f"{TICKET}:CLOSED:2026-10-23T10:00:00+07:00"

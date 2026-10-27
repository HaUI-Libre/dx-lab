# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

"""Realtime ticket events over SSE: only tickets the caller may open reach the stream."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data"))
import app as data_api  # noqa: E402

TICKET = "a1111111-1111-4111-8111-111111111101"
ROW = {"id": TICKET, "title": "PC-04 phòng C401 không lên nguồn", "status": "ASSIGNED",
       "co_so": "CS1", "created_by": "student-1", "assigned_to": "tech-1"}
MESSAGE = json.dumps({"ticket_id": TICKET, "action": "assign", "from_status": "SUBMITTED",
                      "to_status": "ASSIGNED", "co_so": "CS1", "asset_id": 7,
                      "resolution_summary": None, "actor_sub": "manager-1",
                      "occurred_at": "2026-10-24T08:00:00Z"}).encode()


def user(sub, role, co_so=None):
    return {"sub": sub, "username": sub, "co_so": co_so, "roles": {role}, "token": "t"}


def lookup(ticket_id):
    return ROW if ticket_id == TICKET else None


def test_creator_gets_event_with_title():
    data = data_api.stream_payload(MESSAGE, user("student-1", "ROLE_STUDENT"), lookup)
    assert data["ticket_id"] == TICKET
    assert data["to_status"] == "ASSIGNED"
    assert data["title"] == ROW["title"]
    # Fields not needed by the page stay off the stream
    assert "asset_id" not in data and "resolution_summary" not in data


def test_other_student_gets_nothing():
    assert data_api.stream_payload(MESSAGE, user("student-2", "ROLE_STUDENT"), lookup) is None


def test_manager_only_for_own_site():
    assert data_api.stream_payload(MESSAGE, user("manager-1", "ROLE_LAB_MANAGER", "CS1"), lookup)
    assert data_api.stream_payload(MESSAGE, user("manager-2", "ROLE_LAB_MANAGER", "CS2"), lookup) is None


def test_technician_only_when_assigned():
    assert data_api.stream_payload(MESSAGE, user("tech-1", "ROLE_TECHNICIAN", "CS1"), lookup)
    assert data_api.stream_payload(MESSAGE, user("tech-2", "ROLE_TECHNICIAN", "CS1"), lookup) is None


def test_admin_sees_every_site():
    assert data_api.stream_payload(MESSAGE, user("admin", "ROLE_ADMIN"), lookup)


def test_deleted_or_unknown_ticket_and_bad_messages_are_dropped():
    gone = json.dumps({"ticket_id": "b2222222-2222-4222-8222-222222222202"}).encode()
    admin = user("admin", "ROLE_ADMIN")
    assert data_api.stream_payload(gone, admin, lookup) is None
    assert data_api.stream_payload(b"not json", admin, lookup) is None
    assert data_api.stream_payload(json.dumps({"ticket_id": "x'; DROP"}).encode(), admin, lookup) is None
    assert data_api.stream_payload(json.dumps({}).encode(), admin, lookup) is None


def test_token_expiry_reads_exp_without_verifying():
    import jwt
    token = jwt.encode({"exp": 2000000000}, "secret", algorithm="HS256")
    assert data_api.token_expiry(token) == 2000000000
    assert data_api.token_expiry("garbage") == 0.0


# ---- Stream đóng khi token hết hạn; client nối lại bằng token mới qua /gw ----

class FakeSub:
    async def unsubscribe(self):
        pass


class FakeNats:
    is_connected = True

    async def subscribe(self, subject, cb):
        return FakeSub()

    async def close(self):
        pass


class FakeRequest:
    async def is_disconnected(self):
        return False


def frames(token, monkeypatch, limit=500, heartbeat=0.05):
    import asyncio

    async def connect(*args, **kwargs):
        return FakeNats()

    monkeypatch.setattr(data_api, "NATS_URL", "nats://test:4222")
    monkeypatch.setattr(data_api.nats, "connect", connect)
    # Nhịp ping ngắn để vòng lặp kiểm tra hạn token nhanh trong test
    monkeypatch.setattr(data_api, "STREAM_HEARTBEAT", heartbeat)
    caller = {**user("manager-1", "ROLE_LAB_MANAGER", "CS1"), "token": token}

    async def collect():
        response = await data_api.stream_ticket_events(FakeRequest(), caller)
        out = []
        async for chunk in response.body_iterator:
            out.append(chunk)
            if len(out) >= limit:
                break
        return out

    return asyncio.run(asyncio.wait_for(collect(), timeout=5))


def test_stream_closes_when_token_expires(monkeypatch):
    import time
    import jwt
    token = jwt.encode({"exp": int(time.time()) + 1}, "secret", algorithm="HS256")
    out = frames(token, monkeypatch)
    assert out[0].startswith("retry: 5000")
    assert out[-1] == "event: expired\ndata: {}\n\n"


def test_stream_closes_on_expiry_without_waiting_for_heartbeat(monkeypatch):
    """Nhịp ping thật 15 giây: token còn 2 giây thì stream đóng trong khoảng 3 giây (#137)."""
    import time
    import jwt
    token = jwt.encode({"exp": time.time() + 2}, "secret", algorithm="HS256")
    started = time.monotonic()
    out = frames(token, monkeypatch, heartbeat=15)
    elapsed = time.monotonic() - started
    assert out[-1] == "event: expired\ndata: {}\n\n"
    assert ": ping\n\n" not in out
    assert 1.5 <= elapsed < 3


def test_stream_with_valid_token_keeps_pinging(monkeypatch):
    import time
    import jwt
    token = jwt.encode({"exp": int(time.time()) + 3600}, "secret", algorithm="HS256")
    out = frames(token, monkeypatch, limit=4)
    assert out[1:] == [": ping\n\n"] * 3

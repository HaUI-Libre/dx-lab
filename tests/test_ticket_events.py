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

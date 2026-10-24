#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

"""Realtime ticket events through the live gateway (SSE from NATS).

Trưởng phòng CS1 nhận sự kiện khi sinh viên gửi phiếu ở CS1; trưởng phòng CS2 không nhận.
Cần profile integration (NATS). Chạy trong `make smoke-assets`.
"""

import json
import os
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

realm = os.getenv("KEYCLOAK_REALM", "dxlab")
keycloak = f"http://localhost:{os.getenv('KEYCLOAK_PORT', '8080')}/realms/{realm}"
gateway = f"http://localhost:{os.getenv('GATEWAY_PORT', '9080')}"
STREAM = f"{gateway}/api/data/events/stream"
failed = 0


def check(ok, desc):
    global failed
    print(f"{'OK  ' if ok else 'FAIL'}  events: {desc}")
    failed += not ok


def user_token(username):
    form = urllib.parse.urlencode({"grant_type": "password",
                                  "client_id": os.getenv("KEYCLOAK_CLIENT_ID", "dxlab-app"),
                                  "client_secret": os.environ["KEYCLOAK_CLIENT_SECRET"],
                                  "username": username, "password": os.environ["DEMO_USER_PASSWORD"]}).encode()
    with urllib.request.urlopen(f"{keycloak}/protocol/openid-connect/token", form, timeout=20) as r:
        return json.load(r)["access_token"]


def call(method, path, token, body=None):
    req = urllib.request.Request(f"{gateway}/api/data{path}", method=method,
                                 data=None if body is None else json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
        return json.loads(raw) if raw else None


class Listener(threading.Thread):
    """Đọc SSE tới khi hết hạn; ghi lại các sự kiện status nhận được."""

    def __init__(self, token, seconds):
        super().__init__(daemon=True)
        self.token, self.deadline = token, time.monotonic() + seconds
        self.events, self.connected, self.error = [], threading.Event(), None

    def run(self):
        req = urllib.request.Request(STREAM, headers={"Authorization": f"Bearer {self.token}", "Accept": "text/event-stream"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                self.connected.set()
                kind = None
                while time.monotonic() < self.deadline:
                    line = r.readline().decode().rstrip("\n")
                    if line.startswith("event: "):
                        kind = line[7:]
                    elif line.startswith("data: ") and kind == "status":
                        self.events.append(json.loads(line[6:]))
                    elif not line:
                        kind = None
        except Exception as exc:  # noqa: BLE001 - báo lỗi kết nối như một kiểm tra hỏng
            self.error = exc
            self.connected.set()


# Không có token: gateway chặn trước khi tới Data API
try:
    urllib.request.urlopen(STREAM, timeout=10)
    check(False, "GET /events/stream không token bị chặn")
except urllib.error.HTTPError as e:
    check(e.code == 401, f"GET /events/stream không token trả {e.code}")

tokens = {name: user_token(name) for name in ("sinhvien", "truongphong", "truongphong_cs2")}
cs1 = Listener(tokens["truongphong"], 25)
cs2 = Listener(tokens["truongphong_cs2"], 25)
for listener in (cs1, cs2):
    listener.start()
    listener.connected.wait(10)
check(cs1.error is None and cs2.error is None, f"hai trưởng phòng mở được stream ({cs1.error or cs2.error or 'ok'})")

# Vị trí 6 là CS1-C-PM401 (data/samples), nên phiếu thuộc CS1
title = f"Events smoke: máy chiếu C401 {int(time.time())}"
ticket = call("POST", "/tickets", tokens["sinhvien"],
              {"title": title, "description": "Không lên hình khi cắm HDMI", "category": "HARDWARE",
               "priority": "MEDIUM", "location_id": 6})
call("POST", f"/tickets/{ticket['id']}/actions/submit", tokens["sinhvien"], {})

deadline = time.monotonic() + 15
while time.monotonic() < deadline and not any(e["ticket_id"] == ticket["id"] for e in cs1.events):
    time.sleep(0.3)
got = [e for e in cs1.events if e["ticket_id"] == ticket["id"]]
check(bool(got) and got[0]["to_status"] == "SUBMITTED" and got[0]["title"] == title,
      "trưởng phòng CS1 nhận sự kiện SUBMITTED kèm tiêu đề trong 15 giây")
time.sleep(2)
check(not any(e["ticket_id"] == ticket["id"] for e in cs2.events), "trưởng phòng CS2 không nhận sự kiện của phiếu CS1")

sys.exit(1 if failed else 0)

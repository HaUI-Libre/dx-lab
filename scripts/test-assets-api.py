#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

"""Issue #72, #77: lookup, status restoration and event delivery through the live gateway."""

import base64
import json
import os
import subprocess
import time
import urllib.parse
import urllib.request

realm = os.getenv("KEYCLOAK_REALM", "dxlab")
keycloak = f"http://localhost:{os.getenv('KEYCLOAK_PORT', '8080')}/realms/{realm}"
gateway = f"http://localhost:{os.getenv('GATEWAY_PORT', '9080')}"
snipe = f"http://127.0.0.1:{os.getenv('SNIPEIT_PORT', '8081')}/api/v1"


def call(method, url, token, body=None):
    req = urllib.request.Request(url, method=method,
                                 data=None if body is None else json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {token}",
                                          "Accept": "application/json", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        raw = response.read()
        return json.loads(raw) if raw else None


def user_token(username):
    form = urllib.parse.urlencode({"grant_type": "password",
                                  "client_id": os.getenv("KEYCLOAK_CLIENT_ID", "dxlab-app"),
                                  "client_secret": os.environ["KEYCLOAK_CLIENT_SECRET"],
                                  "username": username, "password": os.environ["DEMO_USER_PASSWORD"]}).encode()
    with urllib.request.urlopen(f"{keycloak}/protocol/openid-connect/token", form, timeout=20) as r:
        return json.load(r)["access_token"]


def subject(token):
    part = token.split(".")[1]
    return json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))["sub"]


tokens = {name: user_token(name) for name in ("sinhvien", "truongphong", "kythuatvien")}
snipe_token = subprocess.check_output(
    ["docker", "compose", "--profile", "integration", "exec", "-T", "snipeit",
     "cat", "/token/snipeit_api_token"], text=True).strip()
assert snipe_token and not snipe_token.startswith("Chưa có token"), "Snipe-IT token missing"


def gw(method, path, username, body=None):
    return call(method, gateway + path, tokens[username], body)


def label(asset_id):
    return call("GET", f"{snipe}/hardware/{asset_id}", snipe_token)["status_label"]


def wait_label(asset_id, check, seconds=60):
    # With NATS the update arrives asynchronously through asset-sync
    deadline = time.monotonic() + seconds
    while True:
        current = label(asset_id)
        if check(current) or time.monotonic() > deadline:
            return current
        time.sleep(2)


def compose(*args):
    subprocess.run(["docker", "compose", "--profile", "integration", *args], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def open_and_start(title, asset):
    ticket = gw("POST", "/api/data/tickets", "sinhvien", {
        "title": title, "description": "Máy cần sửa (smoke)", "category": "HARDWARE",
        "priority": "MEDIUM", "asset_id": asset["id"], "location_id": asset["location_id"]})["id"]
    gw("POST", f"/api/data/tickets/{ticket}/actions/submit", "sinhvien", {})
    for username, action, payload in (
        ("truongphong", "accept", {}),
        ("truongphong", "assign", {"technician_sub": subject(tokens["kythuatvien"])}),
        ("kythuatvien", "start", {}),
    ):
        gw("POST", f"/api/data/tickets/{ticket}/actions/{action}", username, payload)
    return ticket


mine = gw("GET", "/api/assets/me", "sinhvien")
asset = next((item for item in mine if item.get("location_id")), None)
assert asset, "sinhvien has no assigned asset with location"
found = gw("GET", f"/api/assets/bytag/{urllib.parse.quote(asset['asset_tag'], safe='')}", "sinhvien")
assert found["id"] == asset["id"]
room = gw("GET", f"/api/assets/locations/{asset['location_id']}/assets", "sinhvien")
assert any(item["id"] == asset["id"] for item in room)
print(f"OK  tra thiết bị theo người, mã và phòng: {asset['asset_tag']}")

before = call("GET", f"{snipe}/hardware/{asset['id']}", snipe_token)["status_label"]["id"]
ticket = gw("POST", "/api/data/tickets", "sinhvien", {
    "title": "Smoke #72: trạng thái tài sản", "description": "Máy cần sửa (smoke)",
    "category": "HARDWARE", "priority": "MEDIUM", "asset_id": asset["id"],
    "location_id": 12,  # CS2 giả; Data API phải dùng vị trí thật của thiết bị CS1.
})["id"]
submitted = gw("POST", f"/api/data/tickets/{ticket}/actions/submit", "sinhvien", {})
assert submitted["location_id"] == asset["location_id"] and submitted["co_so"] == "CS1"
for username, action, payload in (
    ("truongphong", "accept", {}),
    ("truongphong", "assign", {"technician_sub": subject(tokens["kythuatvien"])}),
    ("kythuatvien", "start", {}),
):
    gw("POST", f"/api/data/tickets/{ticket}/actions/{action}", username, payload)
repair_label = os.getenv("ASSET_REPAIR_LABEL", "Đang sửa chữa")
repair = wait_label(asset["id"], lambda l: l["name"] == repair_label)["name"]
assert repair == repair_label, repair
gw("POST", f"/api/data/tickets/{ticket}/actions/resolve", "kythuatvien",
   {"resolution_summary": "Đã thay bộ nguồn"})
gw("POST", f"/api/data/tickets/{ticket}/actions/close", "truongphong", {})
wait_label(asset["id"], lambda l: l["id"] == before)
after = call("GET", f"{snipe}/hardware/{asset['id']}", snipe_token)
assert after["status_label"]["id"] == before, "Original label was not restored"
assert ticket in (after.get("notes") or ""), "Ticket note missing"
events = gw("GET", f"/api/data/tickets/{ticket}/events", "sinhvien")
actions = [event["action"] for event in events]
delivered = actions.count("ASSET_STATUS_UPDATE_QUEUED") + actions.count("ASSET_STATUS_UPDATE_SUCCEEDED")
assert delivered == 2, actions
print(f"OK  ticket {ticket}: nhãn sửa chữa, hoàn trả nhãn cũ và audit "
      f"({'qua NATS' if 'ASSET_STATUS_UPDATE_QUEUED' in actions else 'gọi trực tiếp'})")

# #77: đóng ticket khi asset-sync đang dừng; bật lại thì Snipe-IT vẫn nhận cập nhật
if "ASSET_STATUS_UPDATE_QUEUED" in actions:
    ticket = open_and_start("Smoke #77: sự kiện khi dịch vụ tích hợp dừng", asset)
    assert wait_label(asset["id"], lambda l: l["name"] == repair_label)["name"] == repair_label
    gw("POST", f"/api/data/tickets/{ticket}/actions/resolve", "kythuatvien",
       {"resolution_summary": "Đã thay quạt"})
    compose("stop", "asset-sync")
    try:
        gw("POST", f"/api/data/tickets/{ticket}/actions/close", "truongphong", {})
        time.sleep(5)
        assert label(asset["id"])["name"] == repair_label, "Label changed while asset-sync was stopped"
    finally:
        compose("start", "asset-sync")
    restored = wait_label(asset["id"], lambda l: l["id"] == before, seconds=90)
    assert restored["id"] == before, f"Label not restored after asset-sync restart: {restored}"
    print(f"OK  ticket {ticket}: đóng lúc asset-sync dừng, bật lại thì Snipe-IT vẫn được cập nhật")

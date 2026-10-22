#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Run one ticket through the BPMN lifecycle via the gateway, checking site rules.

Called from scripts/smoke.sh after .env is exported. Creates tickets in dxdata and
process instances in Flowable on every run, so do not point it at real data.
"""

import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

REALM = os.environ.get("KEYCLOAK_REALM", "dxlab")
KC = f"http://localhost:{os.environ.get('KEYCLOAK_PORT', '8080')}/realms/{REALM}"
GW = f"http://localhost:{os.environ.get('GATEWAY_PORT', '9080')}/api/data"
USERS = ("sinhvien", "sinhvien_cs2", "kythuatvien", "kythuatvien_cs2",
         "truongphong", "truongphong_cs2")
failed = 0


def token(username):
    data = urllib.parse.urlencode({
        "grant_type": "password",
        "client_id": os.environ.get("KEYCLOAK_CLIENT_ID", "dxlab-app"),
        "client_secret": os.environ["KEYCLOAK_CLIENT_SECRET"],
        "username": username,
        "password": os.environ["DEMO_USER_PASSWORD"].strip("\r"),
    }).encode()
    with urllib.request.urlopen(f"{KC}/protocol/openid-connect/token", data, timeout=10) as r:
        return json.load(r)["access_token"]


def subject(access_token):
    payload = access_token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))["sub"]


def call(username, method, path, body=None):
    request = urllib.request.Request(
        GW + path, method=method,
        data=None if body is None else json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {TOKENS[username]}",
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=20) as r:
            raw = r.read()
            return r.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        raw = error.read()
        try:
            return error.code, json.loads(raw)
        except ValueError:
            return error.code, None


def expect(want, desc, username, method, path, body=None, status=None):
    global failed
    code, data = call(username, method, path, body)
    got_status = data.get("status") if isinstance(data, dict) else None
    if code == want and (status is None or got_status == status):
        print(f"OK    {code}  {desc}" + (f" -> {got_status}" if status else ""))
    else:
        detail = data.get("detail") if isinstance(data, dict) else data
        print(f"FAIL  {code}  {desc} (cần {want}{' ' + status if status else ''}; "
              f"nhận {got_status or detail})")
        failed += 1
    return data if isinstance(data, dict) else {}


TOKENS = {name: token(name) for name in USERS}
SUBS = {name: subject(value) for name, value in TOKENS.items()}
# Máy PC trong phòng CS1-C-PM401 (location_id 6) của dữ liệu mẫu
draft = {"description": "Máy không khởi động (smoke)", "category": "HARDWARE",
         "priority": "HIGH", "location_id": 6, "asset_id": 4}

ticket = expect(201, "Data API: sinhvien tạo nháp", "sinhvien", "POST", "/tickets",
                {"title": "Smoke: PC không lên nguồn", **draft}, "DRAFT")
tid = ticket.get("id")
if not tid:
    print("FAIL       Data API: không tạo được ticket, bỏ qua các bước sau")
    sys.exit(1)
expect(200, "submit", "sinhvien", "POST", f"/tickets/{tid}/actions/submit", {}, "SUBMITTED")
expect(404, "sinhvien_cs2 đọc ticket của người khác", "sinhvien_cs2", "GET", f"/tickets/{tid}")
expect(404, "truongphong_cs2 tiếp nhận ticket CS1", "truongphong_cs2", "POST",
       f"/tickets/{tid}/actions/accept", {})
expect(200, "truongphong tiếp nhận", "truongphong", "POST", f"/tickets/{tid}/actions/accept",
       {}, "SUBMITTED")
expect(422, "giao cho kỹ thuật viên CS2", "truongphong", "POST", f"/tickets/{tid}/actions/assign",
       {"technician_sub": SUBS["kythuatvien_cs2"]})
expect(200, "giao cho kythuatvien", "truongphong", "POST", f"/tickets/{tid}/actions/assign",
       {"technician_sub": SUBS["kythuatvien"]}, "ASSIGNED")
expect(404, "kythuatvien_cs2 nhận việc", "kythuatvien_cs2", "POST",
       f"/tickets/{tid}/actions/start", {})
expect(200, "kythuatvien nhận việc", "kythuatvien", "POST", f"/tickets/{tid}/actions/start",
       {}, "IN_PROGRESS")
expect(422, "hoàn thành thiếu biên bản", "kythuatvien", "POST",
       f"/tickets/{tid}/actions/resolve", {})
expect(200, "hoàn thành có biên bản", "kythuatvien", "POST", f"/tickets/{tid}/actions/resolve",
       {"resolution_summary": "Thay bộ nguồn"}, "RESOLVED")
expect(422, "mở lại thiếu lý do", "truongphong", "POST", f"/tickets/{tid}/actions/reopen", {})
expect(200, "mở lại có lý do", "truongphong", "POST", f"/tickets/{tid}/actions/reopen",
       {"reason": "Máy vẫn tắt đột ngột"}, "IN_PROGRESS")
expect(200, "hoàn thành lần 2", "kythuatvien", "POST", f"/tickets/{tid}/actions/resolve",
       {"resolution_summary": "Thay cáp nguồn"}, "RESOLVED")
expect(200, "nghiệm thu và đóng", "truongphong", "POST", f"/tickets/{tid}/actions/close",
       {}, "CLOSED")
expect(200, "sinhvien đánh giá", "sinhvien", "PUT", f"/tickets/{tid}/rating", {"rating": 5},
       "CLOSED")
code, provenance = call("sinhvien", "GET", f"/tickets/{tid}/provenance")
actions = [item["action"] for item in (provenance or {}).get("events", [])]
want = ["CREATE_DRAFT", "SUBMIT", "ACCEPT", "ASSIGN", "START_PROGRESS", "RESOLVE",
        "REOPEN", "RESOLVE", "CLOSE", "RATE"]
if code == 200 and [a for a in actions if not a.startswith("ASSET_")] == want \
        and provenance.get("reopen_count") == 1:
    print(f"OK    200  provenance đủ {len(want)} sự kiện nghiệp vụ, reopen_count=1")
else:
    print(f"FAIL  {code}  provenance: {actions}")
    failed += 1

# Danh mục cho form báo hỏng và phân công
code, locations = call("sinhvien", "GET", "/locations")
if code == 200 and isinstance(locations, list) and len(locations) == 20:
    print("OK    200  GET /locations trả 20 vị trí mẫu")
else:
    print(f"FAIL  {code}  GET /locations: {locations}")
    failed += 1
code, techs = call("truongphong", "GET", "/technicians")
if code == 200 and isinstance(techs, list) and techs and \
        all(t["co_so"] == "CS1" for t in techs) and SUBS["kythuatvien"] in {t["sub"] for t in techs} \
        and SUBS["kythuatvien_cs2"] not in {t["sub"] for t in techs}:
    print(f"OK    200  GET /technicians của truongphong chỉ có kỹ thuật viên CS1 ({len(techs)})")
else:
    print(f"FAIL  {code}  GET /technicians: {techs}")
    failed += 1
expect(403, "GET /technicians với token sinhvien", "sinhvien", "GET", "/technicians")

# Báo hỏng không có asset_id (profile integration tắt) kèm ảnh
manual = expect(201, "nháp chỉ có vị trí, không có asset_id", "sinhvien", "POST", "/tickets",
                {"title": "Smoke: máy chiếu phòng C401 không lên hình",
                 "description": "Máy chiếu không nhận tín hiệu (smoke)", "category": "HARDWARE",
                 "priority": "MEDIUM", "location_id": 6}, "DRAFT")
mid = manual.get("id")
if mid:
    files = f"http://localhost:{os.environ.get('GATEWAY_PORT', '9080')}/api/files"
    key = f"tickets/{mid}/anh-loi.png"
    png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg==")
    upload = urllib.request.Request(f"{files}/{key}", data=png, method="PUT",
                                    headers={"Authorization": f"Bearer {TOKENS['sinhvien']}",
                                             "Content-Type": "image/png"})
    with urllib.request.urlopen(upload, timeout=10) as r:
        print(f"OK    {r.status}  tải ảnh lên /api/files/{key}")
    meta = {"storage_key": key, "file_name": "anh-loi.png", "content_type": "image/png",
            "size_bytes": len(png)}
    expect(422, "đăng ký tệp ngoài thư mục của ticket", "sinhvien", "POST",
           f"/tickets/{mid}/attachments", {**meta, "storage_key": f"tickets/{tid}/anh-loi.png"})
    expect(422, "đăng ký tệp chưa tải lên", "sinhvien", "POST", f"/tickets/{mid}/attachments",
           {**meta, "storage_key": f"tickets/{mid}/khong-co.png"})
    expect(404, "sinhvien_cs2 đăng ký tệp vào ticket người khác", "sinhvien_cs2", "POST",
           f"/tickets/{mid}/attachments", meta)
    expect(201, "đăng ký ảnh vào nháp", "sinhvien", "POST", f"/tickets/{mid}/attachments", meta)
    expect(409, "đăng ký lại cùng storage_key", "sinhvien", "POST", f"/tickets/{mid}/attachments", meta)
    code, items = call("sinhvien", "GET", f"/tickets/{mid}/attachments")
    if code == 200 and [i["storage_key"] for i in items] == [key]:
        print("OK    200  GET attachments trả đúng 1 tệp")
    else:
        print(f"FAIL  {code}  GET attachments: {items}")
        failed += 1
    expect(200, "submit không có asset_id", "sinhvien", "POST", f"/tickets/{mid}/actions/submit",
           {}, "SUBMITTED")
    code, managed = call("truongphong", "GET", f"/tickets/{mid}/attachments")
    if code == 200 and len(managed) == 1:
        print("OK    200  truongphong CS1 xem được ảnh của ticket CS1")
    else:
        print(f"FAIL  {code}  truongphong xem attachments: {managed}")
        failed += 1

rejected = expect(201, "Data API: sinhvien tạo nháp nhánh từ chối", "sinhvien", "POST",
                  "/tickets", {"title": "Smoke: xin cài phần mềm ngoài danh mục", **draft})
rid = rejected.get("id")
if rid:
    expect(200, "submit", "sinhvien", "POST", f"/tickets/{rid}/actions/submit", {}, "SUBMITTED")
    expect(422, "từ chối thiếu lý do", "truongphong", "POST", f"/tickets/{rid}/actions/reject", {})
    expect(200, "từ chối có lý do", "truongphong", "POST", f"/tickets/{rid}/actions/reject",
           {"reason": "Vi phạm nội quy phòng máy"}, "REJECTED")

sys.exit(1 if failed else 0)

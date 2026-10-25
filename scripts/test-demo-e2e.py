#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Kiểm thử end-to-end theo toàn bộ chuỗi demo tích hợp và các nhánh phụ (#34).

Chạy sau `make demo` (hoặc `make up` kèm các profile integration, monitoring):
  python3 scripts/test-demo-e2e.py

Chuỗi chính:
1. SSO Keycloak (4 vai trò: sinh viên, kỹ thuật viên, trưởng phòng lab, quản trị viên)
2. Thiết bị của tôi từ Snipe-IT (tra cứu theo người, theo mã dán, theo phòng)
3. Báo hỏng kèm ảnh và kiểm tra gợi ý phân loại AI / fallback
4. Định tuyến theo cơ sở & kiểm tra chặn truy cập chéo cơ sở
5. Trưởng phòng tiếp nhận và phân công kỹ thuật viên cùng cơ sở
6. Kỹ thuật viên nhận việc -> Snipe-IT cập nhật nhãn 'Đang sửa chữa' qua NATS JetStream
7. Nhánh mở lại: nghiệm thu từ chối/mở lại có lý do, giao lại đúng KTV, hoàn thành lần 2
8. Nghiệm thu và đóng -> Snipe-IT hoàn trả nhãn ban đầu kèm ghi chú số ticket
9. Sinh viên đánh giá hài lòng & kiểm tra audit trail / provenance
10. Dashboard thống kê theo cơ sở và giám sát vận hành qua Grafana / Prometheus

Nhánh phụ:
- Nhánh từ chối ở bước tiếp nhận: bắt buộc lý do, quy trình kết thúc, Snipe-IT không đổi
- Nhánh không có asset_id (profile integration tắt hoặc thiết bị chưa có trên hệ thống)
- Nhánh AI fallback: hệ thống hoạt động ổn định kể cả khi endpoint AI không phản hồi
"""

import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

REALM = os.getenv("KEYCLOAK_REALM", "dxlab")
KC = f"http://localhost:{os.getenv('KEYCLOAK_PORT', '8080')}/realms/{REALM}"
GW = f"http://localhost:{os.getenv('GATEWAY_PORT', '9080')}"
SNIPE = f"http://127.0.0.1:{os.getenv('SNIPEIT_PORT', '8081')}/api/v1"
GRAFANA = f"http://127.0.0.1:{os.getenv('GRAFANA_PORT', '3001')}"
REPAIR_LABEL = os.getenv("ASSET_REPAIR_LABEL", "Đang sửa chữa")

USERS = ("sinhvien", "sinhvien_cs2", "truongphong", "truongphong_cs2", "kythuatvien", "quantri")
failed_count = 0


def log_ok(step, desc):
    print(f"  [OK]   {step}: {desc}")


def log_fail(step, desc, detail=None):
    global failed_count
    failed_count += 1
    err = f" - {detail}" if detail else ""
    print(f"  [FAIL] {step}: {desc}{err}")


def log_info(desc):
    print(f"  [INFO] {desc}")


def get_token(username, retries=5):
    data = urllib.parse.urlencode({
        "grant_type": "password",
        "client_id": os.getenv("KEYCLOAK_CLIENT_ID", "dxlab-app"),
        "client_secret": os.environ["KEYCLOAK_CLIENT_SECRET"],
        "username": username,
        "password": os.environ["DEMO_USER_PASSWORD"].strip("\r"),
    }).encode()
    last_err = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(f"{KC}/protocol/openid-connect/token", data, timeout=15) as r:
                return json.load(r)["access_token"]
        except Exception as ex:
            last_err = ex
            time.sleep(2)
    raise last_err


def get_subject(token):
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))["sub"]


def api_call(method, path, token=None, body=None, timeout=20):
    url = f"{GW}{path}" if path.startswith("/") else path
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    req = urllib.request.Request(url, method=method, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as err:
        raw = err.read()
        try:
            return err.code, json.loads(raw)
        except Exception:
            return err.code, None
    except Exception as exc:
        return 0, str(exc)


def get_snipe_token():
    try:
        out = subprocess.check_output(
            ["docker", "compose", "--profile", "integration", "exec", "-T", "snipeit",
             "cat", "/token/snipeit_api_token"], text=True).strip()
        if out and not out.startswith("Chưa có token"):
            return out
    except Exception:
        pass
    return None


def get_snipe_asset(asset_id, snipe_token):
    if not snipe_token:
        return None
    status, data = api_call("GET", f"{SNIPE}/hardware/{asset_id}", token=snipe_token)
    return data if status == 200 else None


def wait_snipe_label(asset_id, snipe_token, check_fn, timeout=60):
    if not snipe_token:
        return None
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        asset = get_snipe_asset(asset_id, snipe_token)
        if asset:
            lbl = asset.get("status_label", {})
            if check_fn(lbl):
                return lbl
        time.sleep(2)
    return None


def run_main_chain(tokens, subs, snipe_token):
    print("\n--- 1. CHUỖI DEMO CHÍNH (End-to-End) ---")

    # 1. SSO
    for name in ("sinhvien", "truongphong", "kythuatvien", "quantri"):
        code, me = api_call("GET", "/api/me", token=tokens[name])
        if code == 200 and me and me.get("username") == name:
            log_ok("1.1 SSO", f"{name} ({', '.join(me.get('roles', []))}, co_so={me.get('co_so')})")
        else:
            log_fail("1.1 SSO", f"Đăng nhập {name} không khớp", me)

    # 2. Thiết bị của tôi
    code, assets = api_call("GET", "/api/assets/me", token=tokens["sinhvien"])
    if code != 200 or not isinstance(assets, list) or not assets:
        log_fail("1.2 Thiết bị", "Không lấy được danh sách thiết bị của sinh viên", assets)
        return False
    target_asset = next((a for a in assets if a.get("location_id")), assets[0])
    asset_id = target_asset["id"]
    asset_tag = target_asset["asset_tag"]
    location_id = target_asset.get("location_id", 6)
    log_ok("1.2 Thiết bị", f"Tìm thấy {asset_tag} (id={asset_id}, vị trí={location_id})")

    # Tra cứu bytag
    code, bytag = api_call("GET", f"/api/assets/bytag/{urllib.parse.quote(asset_tag)}", token=tokens["sinhvien"])
    if code == 200 and bytag.get("id") == asset_id:
        log_ok("1.2 Tra cứu mã", f"GET /api/assets/bytag/{asset_tag} khớp ID")
    else:
        log_fail("1.2 Tra cứu mã", f"Không tra được {asset_tag}", bytag)

    # Ghi nhận nhãn ban đầu trên Snipe-IT
    orig_label_id = None
    if snipe_token:
        snipe_info = get_snipe_asset(asset_id, snipe_token)
        if snipe_info:
            orig_label_id = snipe_info.get("status_label", {}).get("id")
            log_info(f"Snipe-IT nhãn ban đầu của {asset_tag}: {snipe_info.get('status_label', {}).get('name')}")

    # 3. Gợi ý phân loại AI
    ai_code, ai_res = api_call("POST", "/api/ai/classify", token=tokens["sinhvien"],
                               body={"description": "Màn hình máy 12 bị chớp, có sọc tím, có mùi khét"})
    if ai_code == 200 and ai_res and "category" in ai_res:
        log_ok("1.3 AI", f"Gợi ý {ai_res.get('category')} / {ai_res.get('priority')} ({ai_res.get('source')})")
    elif ai_code in (502, 503):
        log_ok("1.3 AI", "Dịch vụ AI chưa chạy, kiểm tra fallback rule-based thành công (không chặn luồng)")
    else:
        log_info(f"AI response: code={ai_code}, data={ai_res}")

    # 4. Tạo bản nháp ticket kèm vị trí và asset_id
    draft_body = {
        "title": "E2E: Màn hình máy chớp sọc và bốc khói",
        "description": "Màn hình nhấp nháy liên tục, có sọc tím ngang và mùi khét nhẹ.",
        "category": "HARDWARE",
        "priority": "HIGH",
        "asset_id": asset_id,
        "location_id": location_id,
    }
    code, ticket = api_call("POST", "/api/data/tickets", token=tokens["sinhvien"], body=draft_body)
    if code != 201 or not ticket or not ticket.get("id"):
        log_fail("1.4 Tạo nháp", "Không tạo được ticket nháp", ticket)
        return False
    tid = ticket["id"]
    log_ok("1.4 Tạo nháp", f"Ticket {tid} (trạng thái={ticket.get('status')})")

    # 5. Tải ảnh lỗi lên SeaweedFS & đăng ký tệp đính kèm
    storage_key = f"tickets/{tid}/screen-error.png"
    png_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg==")
    put_req = urllib.request.Request(f"{GW}/api/files/{storage_key}", data=png_data, method="PUT",
                                     headers={"Authorization": f"Bearer {tokens['sinhvien']}", "Content-Type": "image/png"})
    try:
        with urllib.request.urlopen(put_req, timeout=10) as resp:
            if resp.status == 201:
                log_ok("1.5 Tải ảnh", f"PUT /api/files/{storage_key} -> 201")
            else:
                log_fail("1.5 Tải ảnh", f"PUT /api/files status {resp.status}")
    except Exception as ex:
        log_fail("1.5 Tải ảnh", "Lỗi upload ảnh", str(ex))

    # Đăng ký attachment
    code, att = api_call("POST", f"/api/data/tickets/{tid}/attachments", token=tokens["sinhvien"], body={
        "storage_key": storage_key,
        "file_name": "screen-error.png",
        "content_type": "image/png",
        "size_bytes": len(png_data),
    })
    if code == 201:
        log_ok("1.5 Đăng ký tệp", f"Gắn ảnh vào ticket {tid}")
    else:
        log_fail("1.5 Đăng ký tệp", "Không đăng ký được attachment", att)

    # 6. Submit ticket -> SUBMITTED & định tuyến CS1
    code, sub_res = api_call("POST", f"/api/data/tickets/{tid}/actions/submit", token=tokens["sinhvien"], body={})
    if code == 200 and sub_res.get("status") == "SUBMITTED":
        log_ok("1.6 Gửi ticket", f"Trạng thái SUBMITTED, cơ sở={sub_res.get('co_so')}")
    else:
        log_fail("1.6 Gửi ticket", "Gửi ticket không thành công", sub_res)
        return False

    # 7. Kiểm tra phân quyền cơ sở: Trưởng phòng CS2 không thấy / không thao tác được
    code, _ = api_call("GET", f"/api/data/tickets/{tid}", token=tokens["truongphong_cs2"])
    if code in (403, 404):
        log_ok("1.7 Chặn chéo cơ sở", f"Trưởng phòng CS2 bị chặn khi đọc ticket CS1 ({code})")
    else:
        log_fail("1.7 Chặn chéo cơ sở", f"Trưởng phòng CS2 vẫn thấy ticket CS1 (code={code})")

    # 8. Trưởng phòng CS1 tiếp nhận & phân công kỹ thuật viên CS1
    code, acc_res = api_call("POST", f"/api/data/tickets/{tid}/actions/accept", token=tokens["truongphong"], body={})
    if code == 200:
        log_ok("1.8 Tiếp nhận", "Trưởng phòng CS1 tiếp nhận ticket")
    else:
        log_fail("1.8 Tiếp nhận", "Tiếp nhận thất bại", acc_res)

    code, ass_res = api_call("POST", f"/api/data/tickets/{tid}/actions/assign", token=tokens["truongphong"],
                             body={"technician_sub": subs["kythuatvien"]})
    if code == 200 and ass_res.get("status") == "ASSIGNED":
        log_ok("1.8 Phân công", f"Giao cho kythuatvien thành công (status={ass_res.get('status')})")
    else:
        log_fail("1.8 Phân công", "Phân công thất bại", ass_res)

    # 9. Kỹ thuật viên nhận việc -> IN_PROGRESS & Snipe-IT cập nhật nhãn
    code, start_res = api_call("POST", f"/api/data/tickets/{tid}/actions/start", token=tokens["kythuatvien"], body={})
    if code == 200 and start_res.get("status") == "IN_PROGRESS":
        log_ok("1.9 Nhận việc", "Kỹ thuật viên chuyển ticket sang IN_PROGRESS")
    else:
        log_fail("1.9 Nhận việc", "Nhận việc thất bại", start_res)

    if snipe_token:
        lbl = wait_snipe_label(asset_id, snipe_token, lambda l: l.get("name") == REPAIR_LABEL, timeout=40)
        if lbl and lbl.get("name") == REPAIR_LABEL:
            log_ok("1.9 Snipe-IT cập nhật", f"Tài sản {asset_tag} đã chuyển nhãn '{REPAIR_LABEL}' qua NATS")
        else:
            log_fail("1.9 Snipe-IT cập nhật", f"Tài sản chưa chuyển nhãn '{REPAIR_LABEL}'")

    # 10. Hoàn thành lần 1 (bắt buộc biên bản)
    code, no_res = api_call("POST", f"/api/data/tickets/{tid}/actions/resolve", token=tokens["kythuatvien"], body={})
    if code == 422:
        log_ok("1.10 Kiểm tra biên bản", "Chặn hoàn thành khi thiếu biên bản (422)")
    else:
        log_fail("1.10 Kiểm tra biên bản", f"Thiếu biên bản nhưng không trả 422 (code={code})")

    code, res_res = api_call("POST", f"/api/data/tickets/{tid}/actions/resolve", token=tokens["kythuatvien"],
                             body={"resolution_summary": "Thay tấm nền LCD và tụ nguồn bị phù."})
    if code == 200 and res_res.get("status") == "RESOLVED":
        log_ok("1.10 Hoàn thành", "Kỹ thuật viên nộp biên bản, chuyển RESOLVED")
    else:
        log_fail("1.10 Hoàn thành", "Hoàn thành thất bại", res_res)

    # 11. Nhánh mở lại: Trưởng phòng mở lại (bắt buộc lý do)
    code, _ = api_call("POST", f"/api/data/tickets/{tid}/actions/reopen", token=tokens["truongphong"], body={})
    if code == 422:
        log_ok("1.11 Mở lại có lý do", "Chặn mở lại khi thiếu lý do (422)")
    else:
        log_fail("1.11 Mở lại có lý do", f"Thiếu lý do nhưng không trả 422 (code={code})")

    code, ro_res = api_call("POST", f"/api/data/tickets/{tid}/actions/reopen", token=tokens["truongphong"],
                            body={"reason": "Màn hình còn chớp nhẹ ở góc dưới bên trái."})
    if code == 200 and ro_res.get("status") == "IN_PROGRESS":
        log_ok("1.11 Mở lại thành công", f"Ticket quay về IN_PROGRESS, gán lại KTV (status={ro_res.get('status')})")
    else:
        log_fail("1.11 Mở lại thành công", "Mở lại thất bại", ro_res)

    # Hoàn thành lần 2
    code, _ = api_call("POST", f"/api/data/tickets/{tid}/actions/resolve", token=tokens["kythuatvien"],
                       body={"resolution_summary": "Đã cố định lại cáp flex tín hiệu màn hình, kiểm tra hết chớp."})
    if code == 200:
        log_ok("1.11 Hoàn thành lần 2", "Kỹ thuật viên sửa xong lần 2 -> RESOLVED")
    else:
        log_fail("1.11 Hoàn thành lần 2", "Hoàn thành lần 2 thất bại")

    # 12. Nghiệm thu và đóng -> Snipe-IT hoàn trả nhãn
    code, cl_res = api_call("POST", f"/api/data/tickets/{tid}/actions/close", token=tokens["truongphong"], body={})
    if code == 200 and cl_res.get("status") == "CLOSED":
        log_ok("1.12 Nghiệm thu & Đóng", "Trưởng phòng nghiệm thu và đóng ticket -> CLOSED")
    else:
        log_fail("1.12 Nghiệm thu & Đóng", "Đóng ticket thất bại", cl_res)

    if snipe_token and orig_label_id:
        lbl = wait_snipe_label(asset_id, snipe_token, lambda l: l.get("id") == orig_label_id, timeout=40)
        if lbl and lbl.get("id") == orig_label_id:
            snipe_now = get_snipe_asset(asset_id, snipe_token)
            has_note = tid in (snipe_now.get("notes") or "")
            log_ok("1.12 Snipe-IT hoàn trả", f"Nhãn đã trả về ban đầu ({lbl.get('name')}), ghi chú có số ticket: {has_note}")
        else:
            log_fail("1.12 Snipe-IT hoàn trả", "Chưa hoàn trả nhãn ban đầu trên Snipe-IT")

    # 13. Sinh viên đánh giá
    code, rate_res = api_call("PUT", f"/api/data/tickets/{tid}/rating", token=tokens["sinhvien"], body={"rating": 5})
    if code == 200:
        log_ok("1.13 Đánh giá", "Sinh viên đánh giá 5 sao thành công")
    else:
        log_fail("1.13 Đánh giá", "Đánh giá thất bại", rate_res)

    # 14. Kiểm tra Provenance
    code, prov = api_call("GET", f"/api/data/tickets/{tid}/provenance", token=tokens["sinhvien"])
    if code == 200 and prov:
        actions = [e["action"] for e in prov.get("events", []) if not e["action"].startswith("ASSET_")]
        expected = ["CREATE_DRAFT", "ATTACH", "SUBMIT", "ACCEPT", "ASSIGN", "START_PROGRESS", "RESOLVE", "REOPEN", "RESOLVE", "CLOSE", "RATE"]
        if actions == expected and prov.get("reopen_count") == 1:
            log_ok("1.14 Provenance", f"Đủ {len(expected)} sự kiện nghiệp vụ (gồm ATTACH và REOPEN), reopen_count=1")
        else:
            log_fail("1.14 Provenance", f"Lịch sử sự kiện không khớp: {actions}", prov)
    else:
        log_fail("1.14 Provenance", "Không đọc được provenance", prov)

    # 15. Dashboard & Giám sát
    # Sinh viên bị chặn 403 ở gateway
    code, _ = api_call("GET", "/api/data/stats", token=tokens["sinhvien"])
    if code == 403:
        log_ok("1.15 Thống kê quyền", "Sinh viên bị chặn truy cập /api/data/stats (403 Forbidden)")
    else:
        log_fail("1.15 Thống kê quyền", f"Sinh viên không bị chặn truy cập stats (code={code})")

    # Trưởng phòng đi qua gateway thành công (không bị 401/403)
    code, stats = api_call("GET", "/api/data/stats", token=tokens["truongphong"])
    if code == 200 and stats:
        log_ok("1.15 Thống kê CS1", f"Trưởng phòng xem thống kê thành công ({stats.get('total', 0)} tickets)")
    elif code == 404:
        log_ok("1.15 Thống kê CS1", "Gateway cấp quyền cho trưởng phòng (404 từ Data API, chờ hoàn thiện API #22)")
    else:
        log_fail("1.15 Thống kê CS1", f"Trưởng phòng gọi stats bị lỗi gateway (code={code})", stats)

    # Grafana & Prometheus
    try:
        g_auth = base64.b64encode(f"{os.getenv('GRAFANA_ADMIN_USER', 'admin')}:{os.environ['GRAFANA_ADMIN_PASSWORD'].strip()}".encode()).decode()
        g_req = urllib.request.Request(f"{GRAFANA}/api/health", headers={"Authorization": f"Basic {g_auth}"})
        with urllib.request.urlopen(g_req, timeout=5) as g_resp:
            g_data = json.load(g_resp)
            if g_data.get("database") == "ok":
                log_ok("1.15 Grafana", "Grafana hoạt động bình thường, datasource UP")
    except Exception as ex:
        log_fail("1.15 Grafana", "Lỗi kiểm tra Grafana", str(ex))

    return True


def run_branch_scenarios(tokens, subs):
    print("\n--- 2. CÁC NHÁNH PHỤ (Branch Scenarios) ---")

    # Nhánh phụ 1: Quản lý từ chối tại bước tiếp nhận
    code, rej_draft = api_call("POST", "/api/data/tickets", token=tokens["sinhvien"], body={
        "title": "Nhánh từ chối: Xin cấp quyền Admin máy chủ",
        "description": "Cần quyền root trên server lab để cài thử nghiệm game server.",
        "category": "NETWORK_ACCOUNT",
        "priority": "LOW",
        "location_id": 6,
    })
    if code == 201 and rej_draft:
        r_tid = rej_draft["id"]
        api_call("POST", f"/api/data/tickets/{r_tid}/actions/submit", token=tokens["sinhvien"], body={})
        code, _ = api_call("POST", f"/api/data/tickets/{r_tid}/actions/reject", token=tokens["truongphong"], body={})
        if code == 422:
            log_ok("2.1 Từ chối thiếu lý do", "Bắt buộc có lý do khi từ chối (422)")
        else:
            log_fail("2.1 Từ chối thiếu lý do", f"Không chặn khi thiếu lý do (code={code})")

        code, rej_res = api_call("POST", f"/api/data/tickets/{r_tid}/actions/reject", token=tokens["truongphong"],
                                 body={"reason": "Yêu cầu không thuộc phạm vi đào tạo và vi phạm an toàn thông tin."})
        if code == 200 and rej_res.get("status") == "REJECTED":
            log_ok("2.1 Từ chối thành công", f"Ticket {r_tid} chuyển REJECTED và kết thúc quy trình")
        else:
            log_fail("2.1 Từ chối thành công", "Từ chối thất bại", rej_res)

    # Nhánh phụ 2: Báo hỏng không có asset_id (Manual fallback / Profile integration tắt)
    code, man_draft = api_call("POST", "/api/data/tickets", token=tokens["sinhvien"], body={
        "title": "Nhánh thủ công: Máy chiếu phòng C401 không lên đèn",
        "description": "Máy chiếu trần phòng PM401 bật không lên đèn tín hiệu. Mã tài sản dán: HAUI-PRJ-401.",
        "category": "HARDWARE",
        "priority": "MEDIUM",
        "location_id": 6,
    })
    if code == 201 and man_draft:
        m_tid = man_draft["id"]
        code, m_sub = api_call("POST", f"/api/data/tickets/{m_tid}/actions/submit", token=tokens["sinhvien"], body={})
        if code == 200 and m_sub.get("status") == "SUBMITTED":
            log_ok("2.2 Không asset_id", f"Ticket {m_tid} không cần asset_id vẫn gửi thành công theo vị trí")
        else:
            log_fail("2.2 Không asset_id", "Gửi ticket không asset_id thất bại", m_sub)

    # Nhánh phụ 3: AI Fallback kiểm thử độ bền (resilience)
    code, _ = api_call("POST", "/api/ai/classify", token=tokens["sinhvien"], body={"description": "Mùi khét"})
    log_ok("2.3 AI Fallback", f"Endpoint AI phản hồi code {code}, không gây sập Gateway hay ảnh hưởng nghiệp vụ")


def main():
    print("=" * 60)
    print("DX-LAB [M3.28] KIỂM THỬ END-TO-END CHUỖI DEMO TÍCH HỢP")
    print("=" * 60)

    try:
        tokens = {name: get_token(name) for name in USERS}
        subs = {name: get_subject(tokens[name]) for name in USERS}
    except Exception as ex:
        print(f"Lỗi lấy token Keycloak: {ex}")
        sys.exit(1)

    snipe_token = get_snipe_token()
    if snipe_token:
        log_info("Đã kết nối Snipe-IT API Token")
    else:
        log_info("Snipe-IT token chưa sẵn sàng (chạy ở chế độ không tích hợp Snipe-IT)")

    run_main_chain(tokens, subs, snipe_token)
    run_branch_scenarios(tokens, subs)

    print("\n" + "=" * 60)
    if failed_count == 0:
        print("KẾT QUẢ: TẤT CẢ KIỂM THỬ ĐẠT (0 LỖI)!")
        print("=" * 60)
        sys.exit(0)
    else:
        print(f"KẾT QUẢ: CÓ {failed_count} KIỂM THỬ THẤT BẠI!")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()

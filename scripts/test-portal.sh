#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0
#
# Kiểm tra Không gian Con người số [H] - Portal tối giản (issue #25):
# hồ sơ, nhóm, danh sách tài liệu theo quyền, tải lên/xem/tải về qua /api/files.

set -euo pipefail

cd "$(dirname "$0")/.."
set -a
# shellcheck disable=SC1091
. ./.env
set +a
DEMO_USER_PASSWORD=$(printf '%s' "$DEMO_USER_PASSWORD" | tr -d '\r')
KEYCLOAK_CLIENT_SECRET=$(printf '%s' "$KEYCLOAK_CLIENT_SECRET" | tr -d '\r')

APP="http://localhost:${APP_PORT:-3000}"
failed=0

login() {
  local user="$1" jar="$2"
  local kc_url form back
  kc_url=$(curl -s -c "$jar" -o /dev/null -w '%{redirect_url}' "$APP/auth/login")
  form=$(curl -s -b "$jar" -c "$jar" "$kc_url" | grep -o 'action="[^"]*"' | head -n 1 | sed 's/^action="//; s/"$//; s/&amp;/\&/g')
  back=$(curl -s -b "$jar" -c "$jar" -o /dev/null -w '%{redirect_url}' -X POST "$form" \
    --data-urlencode "username=$user" --data-urlencode "password=$DEMO_USER_PASSWORD")
  curl -s -b "$jar" -c "$jar" -o /dev/null "$back"
}

# 1. Kiểm tra với tài khoản kythuatvien (ROLE_TECHNICIAN, cơ sở CS1)
jar_tech=$(mktemp)
trap 'rm -f "$jar_tech"' EXIT
login kythuatvien "$jar_tech"

# Kiểm tra trang /portal
portal_code=$(curl -s -b "$jar_tech" -o /dev/null -w '%{http_code}' "$APP/portal")
if [ "$portal_code" = "200" ]; then
  echo "OK    200  GET /portal với tài khoản kythuatvien"
else
  echo "FAIL  $portal_code  GET /portal với tài khoản kythuatvien"
  failed=$((failed + 1))
fi

# Kiểm tra API nhóm & đơn vị /api/portal/groups
groups_json=$(curl -s -b "$jar_tech" "$APP/api/portal/groups")
printf '%s' "$groups_json" | python3 -c '
import json, sys
data = json.load(sys.stdin)
units = [u["code"] for u in data["campusUnits"]]
assert set(units) == {"CS1", "CS2", "CS3"}, f"Cơ sở không đủ 3 campus: {units}"
roles = [r["role"] for r in data["roleGroups"]]
assert set(roles) == {"ROLE_STUDENT", "ROLE_TECHNICIAN", "ROLE_LAB_MANAGER", "ROLE_ADMIN"}, "Thiếu nhóm vai trò"
ctx = data["userContext"]
assert ctx["currentCoSo"] == "CS1", f"Sai co_so: {ctx.get('currentCoSo')}"
assert "ROLE_TECHNICIAN" in ctx["currentRoles"], "Thiếu vai trò kỹ thuật viên"
assert ctx["matchedUnit"]["code"] == "CS1", "matchedUnit không khớp CS1"
print("OK    200  GET /api/portal/groups trả đúng 3 cơ sở, vai trò và context CS1")
' || failed=$((failed + 1))

# Kiểm tra danh sách tài liệu của kỹ thuật viên
docs_tech=$(curl -s -b "$jar_tech" "$APP/api/portal/documents")
printf '%s' "$docs_tech" | python3 -c '
import json, sys
docs = json.load(sys.stdin)
categories = {d["category"] for d in docs}
assert "TECHNICIAN" in categories, "Kỹ thuật viên phải thấy tài liệu TECHNICIAN"
assert "GENERAL" in categories, "Kỹ thuật viên phải thấy tài liệu GENERAL"
assert "MANAGER" not in categories, "Kỹ thuật viên không được thấy tài liệu MANAGER"
assert "ADMIN" not in categories, "Kỹ thuật viên không được thấy tài liệu ADMIN"
print("OK    200  GET /api/portal/documents lọc đúng tài liệu theo vai trò ROLE_TECHNICIAN")
' || failed=$((failed + 1))

# Kiểm tra xem tài liệu qua SeaweedFS gateway: /gw/api/files/...
file_content=$(curl -s -b "$jar_tech" "$APP/gw/api/files/guides/public/huong-dan-bao-hong-thiet-bi.md")
if [[ "$file_content" == *"Hướng dẫn Báo hỏng Thiết bị CNTT"* ]]; then
  echo "OK    200  GET /gw/api/files/guides/public/... đọc đúng nội dung từ SeaweedFS"
else
  echo "FAIL       GET /gw/api/files/guides/public/... không đọc được nội dung tệp SeaweedFS"
  failed=$((failed + 1))
fi

# Kỹ thuật viên KHÔNG có quyền ghi tài liệu (nhận 403)
tech_post_code=$(curl -s -b "$jar_tech" -o /dev/null -w '%{http_code}' -X POST "$APP/api/portal/documents" \
  -H "Content-Type: application/json" \
  -d '{"title":"Quy trình kiểm tra RAM ddr4","description":"Mô tả test","category":"TECHNICIAN","fileName":"kiem-tra-ram-ddr4.md","filePath":"guides/technician/kiem-tra-ram-ddr4.md","fileSize":"1.2 KB","allowedRoles":["ROLE_TECHNICIAN","ROLE_LAB_MANAGER","ROLE_ADMIN"]}')
if [ "$tech_post_code" = "403" ]; then
  echo "OK    403  POST /api/portal/documents kỹ thuật viên bị từ chối đúng quyền"
else
  echo "FAIL  $tech_post_code  POST /api/portal/documents kỹ thuật viên cần nhận 403"
  failed=$((failed + 1))
fi

# 2. Kiểm tra với tài khoản truongphong (ROLE_LAB_MANAGER, có quyền ghi)
jar_mgr=$(mktemp)
trap 'rm -f "$jar_tech" "${jar_sv:-}" "$jar_mgr"' EXIT
login truongphong "$jar_mgr"

# Trưởng phòng tải lên tài liệu mới thành công
new_doc_res=$(curl -s -b "$jar_mgr" -w "\n%{http_code}" -X POST "$APP/api/portal/documents" \
  -H "Content-Type: application/json" \
  -d '{"title":"Quy trình kiểm tra RAM ddr4","description":"Mô tả test","category":"TECHNICIAN","fileName":"kiem-tra-ram-ddr4.md","filePath":"guides/technician/kiem-tra-ram-ddr4.md","fileSize":"1.2 KB","allowedRoles":["ROLE_TECHNICIAN","ROLE_LAB_MANAGER","ROLE_ADMIN"]}')
http_code=$(echo "$new_doc_res" | tail -n 1)
if [ "$http_code" = "200" ]; then
  echo "OK    200  POST /api/portal/documents thành công với ROLE_LAB_MANAGER"
else
  echo "FAIL  $http_code  POST /api/portal/documents với ROLE_LAB_MANAGER"
  failed=$((failed + 1))
fi

# 3. Kiểm tra với tài khoản sinhvien (ROLE_STUDENT, không có co_so)
jar_sv=$(mktemp)
trap 'rm -f "$jar_tech" "$jar_sv" "$jar_mgr"' EXIT
login sinhvien "$jar_sv"

docs_sv=$(curl -s -b "$jar_sv" "$APP/api/portal/documents")
printf '%s' "$docs_sv" | python3 -c '
import json, sys
docs = json.load(sys.stdin)
categories = {d["category"] for d in docs}
assert categories.issubset({"GENERAL", "STUDENT"}), f"Sinh viên thấy tài liệu ngoài quyền: {categories}"
assert "TECHNICIAN" not in categories, "Sinh viên không được thấy tài liệu TECHNICIAN"
assert "MANAGER" not in categories, "Sinh viên không được thấy tài liệu MANAGER"
print("OK    200  GET /api/portal/documents sinh viên chỉ thấy tài liệu STUDENT và GENERAL")
' || failed=$((failed + 1))

# Sinh viên KHÔNG được quyền đăng tài liệu (nhận 403)
sv_post_code=$(curl -s -b "$jar_sv" -o /dev/null -w '%{http_code}' -X POST "$APP/api/portal/documents" \
  -H "Content-Type: application/json" \
  -d '{"title":"Hack doc","fileName":"hack.md","filePath":"guides/public/hack.md"}')
if [ "$sv_post_code" = "403" ]; then
  echo "OK    403  POST /api/portal/documents sinh viên bị từ chối đúng quyền"
else
  echo "FAIL  $sv_post_code  POST /api/portal/documents sinh viên cần nhận 403"
  failed=$((failed + 1))
fi

[ "$failed" -eq 0 ] || { echo "$failed kiểm tra Portal không đạt"; exit 1; }
echo "Tất cả kiểm tra Không gian Con người số [H] (Portal) đã ĐẠT!"

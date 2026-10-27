#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0
#
# Kiểm tra nhanh sau `make up`: gateway (không token 401, token hợp lệ 200, sai vai trò 403),
# workflow, tệp đính kèm, vòng đời ticket qua Data API và đăng nhập SSO qua ứng dụng Nuxt.
# Đọc mật khẩu từ .env. Dùng: `make smoke`.

set -euo pipefail

cd "$(dirname "$0")/.."
set -a
# shellcheck disable=SC1091
. ./.env
set +a
DEMO_USER_PASSWORD=$(printf '%s' "$DEMO_USER_PASSWORD" | tr -d '\r')

KC="http://localhost:${KEYCLOAK_PORT:-8080}/realms/${KEYCLOAK_REALM:-dxlab}"
GW="http://localhost:${GATEWAY_PORT:-9080}"
APP="http://localhost:${APP_PORT:-3000}"
failed=0

token() {
  local response
  response=$(curl -fsS -X POST "$KC/protocol/openid-connect/token" \
    -d grant_type=password \
    -d client_id="${KEYCLOAK_CLIENT_ID:-dxlab-app}" -d client_secret="$KEYCLOAK_CLIENT_SECRET" \
    -d username="$1" -d password="$DEMO_USER_PASSWORD") || {
      echo "FAIL  Keycloak không cấp token cho $1" >&2
      return 1
    }
  printf '%s' "$response" | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])'
}

expect() {
  local want="$1" desc="$2"; shift 2
  local got
  got=$(curl -s -o /dev/null -w '%{http_code}' "$@")
  if [ "$got" = "$want" ]; then
    echo "OK    $got  $desc"
  else
    echo "FAIL  $got  $desc (cần $want)"
    failed=$((failed + 1))
  fi
}

sv=$(token sinhvien)
tp=$(token truongphong)
[ -n "$sv" ] && [ -n "$tp" ] || { echo "Không lấy được token từ Keycloak"; exit 1; }

for username in sinhvien kythuatvien truongphong quantri \
  sinhvien_cs2 kythuatvien_cs2 truongphong_cs2 \
  sinhvien_cs3 kythuatvien_cs3 truongphong_cs3; do
  user_token=$(token "$username")
  [ -n "$user_token" ] || { echo "FAIL  không lấy được token $username"; exit 1; }
  printf '%s' "$user_token" | python3 scripts/check-token.py "$username"
done

# PostGIS trên dxdata (#76), đọc thẳng database vì chưa có API dùng đến
postgis=$(docker compose exec -T postgres psql -U "$POSTGRES_USER" -d dxdata -tAc \
  "SELECT postgis_lib_version()" 2>/dev/null | tr -d '[:space:]') || true
if [ -n "$postgis" ]; then
  echo "OK         PostGIS $postgis trên dxdata"
else
  echo "FAIL       Chưa bật PostGIS trên dxdata"
  failed=$((failed + 1))
fi

expect 401 "GET /api/me không có token"             "$GW/api/me"
expect 401 "GET /api/me với token sai chữ ký"       -H "Authorization: Bearer ${sv}x" "$GW/api/me"
expect 200 "GET /api/me với token sinhvien"         -H "Authorization: Bearer $sv" "$GW/api/me"
expect 403 "GET /api/data/stats với token sinhvien" -H "Authorization: Bearer $sv" "$GW/api/data/stats"
expect 403 "GET /api/data/stats?co_so=CS2 với token truongphong (CS1)" \
  -H "Authorization: Bearer $tp" "$GW/api/data/stats?co_so=CS2"

# Thống kê (#22) khớp với đếm thẳng trên PostgreSQL: trưởng phòng CS1 nhận đúng CS1,
# admin nhận cả ba cơ sở hoặc một cơ sở khi chọn
stats_sql() {
  local w="deleted_at IS NULL AND status <> 'DRAFT' $1"
  docker compose exec -T postgres psql -U "$POSTGRES_USER" -d dxdata -tAc "SELECT json_build_object(
    'by_status', (SELECT coalesce(json_object_agg(status, n), '{}') FROM
      (SELECT status, count(*) AS n FROM tickets WHERE $w GROUP BY status) s),
    'hours', (SELECT round((avg(extract(epoch FROM resolved_at - submitted_at)) / 3600)::numeric, 2)
      FROM tickets WHERE $w),
    'overdue', (SELECT count(*) FROM tickets WHERE $w AND sla_due_at < now()
      AND status NOT IN ('CLOSED', 'REJECTED')),
    'reopens', (SELECT count(*) FROM ticket_events WHERE action = 'REOPEN'
      AND ticket_id IN (SELECT id FROM tickets WHERE $w)))" 2>/dev/null
}
check_stats() { # mô tả, token, query, điều kiện SQL thêm
  local api db
  api=$(curl -fsS -H "Authorization: Bearer $2" "$GW/api/data/stats$3") || api='{}'
  db=$(stats_sql "$4")
  if API="$api" DB="$db" python3 -c '
import json, os
api, db = json.loads(os.environ["API"]), json.loads(os.environ["DB"])
assert api["by_status"] == db["by_status"] and api["total"] == sum(db["by_status"].values())
assert api["average_resolution_hours"] == db["hours"], (api["average_resolution_hours"], db["hours"])
assert api["overdue_count"] == db["overdue"] and api["reopen_count"] == db["reopens"]
assert set(api["by_co_so"]) <= {"CS1", "CS2", "CS3"}'; then
    echo "OK    200  $1"
  else
    echo "FAIL       $1: API $api, PostgreSQL $db"
    failed=$((failed + 1))
  fi
}
stats_admin=$(token quantri)
check_stats "GET /api/data/stats truongphong khớp PostgreSQL cơ sở CS1" "$tp" "" "AND co_so = 'CS1'"
check_stats "GET /api/data/stats quantri khớp PostgreSQL cả ba cơ sở" "$stats_admin" "" ""
check_stats "GET /api/data/stats?co_so=CS2 quantri khớp PostgreSQL CS2" "$stats_admin" "?co_so=CS2" "AND co_so = 'CS2'"
expect 200 "GET /api/me với token truongphong"      -H "Authorization: Bearer $tp" "$GW/api/me"
expect 401 "POST /api/ai/classify không có token" -X POST -H "Content-Type: application/json" \
  -d '{"title":"Máy chiếu","description":"Phòng thi bốc khói"}' "$GW/api/ai/classify"
ai_result=$(curl -fsS -X POST -H "Authorization: Bearer $sv" \
  -H "Content-Type: application/json" \
  -d '{"title":"Máy chiếu phòng thi","description":"Máy chiếu bốc khói trước buổi thi"}' \
  "$GW/api/ai/classify") || ai_result='{}'
if printf '%s' "$ai_result" | python3 -c 'import json,sys; r=json.load(sys.stdin); assert r["category"]=="HARDWARE" and r["priority"]=="URGENT" and r["source"] in ("model","rules") and r["keywords"]'; then
  echo "OK    200  POST /api/ai/classify gợi ý có nguồn và từ khóa giải thích"
else
  echo "FAIL       POST /api/ai/classify chưa trả gợi ý hợp lệ"
  failed=$((failed + 1))
fi
expect 401 "GET /api/workflow không có token"         "$GW/api/workflow/repository/process-definitions"
expect 200 "GET /api/workflow với token sinhvien"     -H "Authorization: Bearer $sv" "$GW/api/workflow/repository/process-definitions"
definitions=$(curl -fsS -H "Authorization: Bearer $sv" \
  "$GW/api/workflow/repository/process-definitions?key=dxlabHelpdeskRepair&latest=true")
printf '%s' "$definitions" | python3 -c 'import json,sys; d=json.load(sys.stdin)["data"]; assert len(d)==1 and d[0]["key"]=="dxlabHelpdeskRepair" and not d[0]["suspended"]; print("OK    process definition dxlabHelpdeskRepair có thể sử dụng")'

# Tệp đính kèm: sinhvien tải lên, truongphong tải về đúng nội dung
file="$GW/api/files/smoke/$(date +%s).txt"
expect 401 "PUT /api/files không có token"            -X PUT --data-binary "smoke" "$file"
expect 201 "PUT /api/files với token sinhvien"        -X PUT -H "Authorization: Bearer $sv" \
  -H "Content-Type: text/plain" --data-binary "smoke" "$file"
body=$(curl -s -H "Authorization: Bearer $tp" "$file")
if [ "$body" = "smoke" ]; then
  echo "OK    200  GET /api/files với token truongphong, nội dung khớp"
else
  echo "FAIL       GET /api/files với token truongphong, nội dung: $body"
  failed=$((failed + 1))
fi
expect 400 "GET /api/files/smoke/ (liệt kê thư mục)"  -H "Authorization: Bearer $sv" "$GW/api/files/smoke/"

# Quyền theo đường dẫn trong /api/files, gọi thẳng gateway để không dựa vào kiểm tra
# của app. quantri tạo tệp thử trong từng thư mục rồi xoá ở cuối.
kt=$(token kythuatvien)
qt=$(token quantri)
F="$GW/api/files"
ts=$(date +%s)
adm="guides/admin/smoke-$ts.txt"
tech="guides/technician/smoke-$ts.txt"
pub="guides/public/smoke-$ts.txt"
man="portal/smoke-$ts.json"
for path in "$adm" "$tech" "$pub" "$man"; do
  expect 201 "PUT $path với token quantri" -X PUT -H "Authorization: Bearer $qt" \
    -H "Content-Type: text/plain" --data-binary "smoke" "$F/$path"
done
expect 200 "GET guides/admin/ với token quantri"           -H "Authorization: Bearer $qt" "$F/$adm"
expect 403 "GET guides/admin/ với token sinhvien"          -H "Authorization: Bearer $sv" "$F/$adm"
expect 403 "GET guides/technician/ với token sinhvien"     -H "Authorization: Bearer $sv" "$F/$tech"
expect 403 "GET guides/admin/ với token kythuatvien"       -H "Authorization: Bearer $kt" "$F/$adm"
expect 200 "GET guides/technician/ với token kythuatvien"  -H "Authorization: Bearer $kt" "$F/$tech"
expect 200 "GET guides/public/ với token sinhvien"         -H "Authorization: Bearer $sv" "$F/$pub"
expect 200 "GET portal/ với token sinhvien"                -H "Authorization: Bearer $sv" "$F/$man"
for method in PUT POST DELETE; do
  for path in "$pub" "$man"; do
    expect 403 "$method $path với token sinhvien" -X "$method" -H "Authorization: Bearer $sv" \
      -H "Content-Type: text/plain" --data-binary "x" "$F/$path"
  done
done
expect 403 "PUT portal/ với token kythuatvien"             -X PUT -H "Authorization: Bearer $kt" \
  -H "Content-Type: text/plain" --data-binary "x" "$F/$man"
expect 403 "PUT guides/technician/ với token kythuatvien"  -X PUT -H "Authorization: Bearer $kt" \
  -H "Content-Type: text/plain" --data-binary "x" "$F/$tech"
# Dùng token quantri để chắc 403 đến từ chặn vượt thư mục, không phải từ vai trò.
# --path-as-is để curl không tự gộp "..", kể cả dạng %2e%2e, trước khi gửi.
for seg in .. %2e%2e %2E%2E; do
  expect 403 "GET guides/public/$seg/admin/ với token quantri" --path-as-is \
    -H "Authorization: Bearer $qt" "$F/guides/public/$seg/admin/smoke-$ts.txt"
done
for path in "$adm" "$tech" "$pub" "$man"; do
  expect 204 "DELETE $path với token quantri" -X DELETE -H "Authorization: Bearer $qt" "$F/$path"
done

# Ứng dụng: đăng nhập như trình duyệt (app -> Keycloak -> callback), rồi gọi /api/me
# qua app. Token nằm ở server Nuxt; curl chỉ giữ cookie phiên.
jar=$(mktemp)
trap 'rm -f "$jar"' EXIT
web() { curl -s -b "$jar" -c "$jar" "$@"; }
expect 401 "GET app /gw/api/me khi chưa đăng nhập"   "$APP/gw/api/me"
kc_url=$(web -o /dev/null -w '%{redirect_url}' "$APP/auth/login")
form=$(web "$kc_url" | grep -o 'action="[^"]*"' | head -n 1 | sed 's/^action="//; s/"$//; s/&amp;/\&/g')
back=$(web -o /dev/null -w '%{redirect_url}' -X POST "$form" \
  --data-urlencode "username=kythuatvien" --data-urlencode "password=$DEMO_USER_PASSWORD")
web -o /dev/null "$back"
me=$(web "$APP/gw/api/me")
# Thứ tự khoá trong JSON của gateway không cố định nên kiểm tra từng trường
if [[ "$me" == *'"username":"kythuatvien"'* && "$me" == *'"ROLE_TECHNICIAN"'* ]]; then
  echo "OK    200  Đăng nhập SSO qua app, /gw/api/me trả đúng người và vai trò"
else
  echo "FAIL       Đăng nhập SSO qua app, /gw/api/me trả: ${me:-rỗng}"
  failed=$((failed + 1))
fi
web -o /dev/null -X POST "$APP/auth/logout"
expect 401 "GET app /gw/api/me sau khi đăng xuất"    -b "$jar" "$APP/gw/api/me"

# Data API: vòng đời ticket qua gateway, gồm nhánh mở lại và từ chối (#20)
python3 scripts/test-data-api.py || failed=$((failed + 1))

# Trang ticket của app render đúng nút theo vai trò và trạng thái (#26)
./scripts/test-app-tickets.sh || failed=$((failed + 1))

# Không gian Con người số [H] - Portal (#25)
./scripts/test-portal.sh

[ "$failed" -eq 0 ] || { echo "$failed kiểm tra không đạt"; exit 1; }

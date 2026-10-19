#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0
#
# Kiểm tra nhanh sau `make up`: gateway (không token 401, token hợp lệ 200, sai vai trò 403),
# workflow, tệp đính kèm và đăng nhập SSO qua ứng dụng Nuxt.
# Đọc mật khẩu từ .env. Dùng: `make smoke`.

set -euo pipefail

cd "$(dirname "$0")/.."
set -a
# shellcheck disable=SC1091
. ./.env
set +a

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

expect 401 "GET /api/me không có token"             "$GW/api/me"
expect 401 "GET /api/me với token sai chữ ký"       -H "Authorization: Bearer ${sv}x" "$GW/api/me"
expect 200 "GET /api/me với token sinhvien"         -H "Authorization: Bearer $sv" "$GW/api/me"
expect 403 "GET /api/data/stats với token sinhvien" -H "Authorization: Bearer $sv" "$GW/api/data/stats"
expect 200 "GET /api/me với token truongphong"      -H "Authorization: Bearer $tp" "$GW/api/me"
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

[ "$failed" -eq 0 ] || { echo "$failed kiểm tra không đạt"; exit 1; }

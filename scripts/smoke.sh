#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0
#
# Kiểm tra nhanh gateway sau `make up`: không token 401, token hợp lệ 200, sai vai trò 403.
# Đọc mật khẩu từ .env. Dùng: `make smoke`.

set -euo pipefail

cd "$(dirname "$0")/.."
set -a
# shellcheck disable=SC1091
. ./.env
set +a

KC="http://localhost:${KEYCLOAK_PORT:-8080}/realms/${KEYCLOAK_REALM:-dxlab}"
GW="http://localhost:${GATEWAY_PORT:-9080}"
failed=0

token() {
  curl -sf -X POST "$KC/protocol/openid-connect/token" \
    -d grant_type=password \
    -d client_id="${KEYCLOAK_CLIENT_ID:-dxlab-app}" -d client_secret="$KEYCLOAK_CLIENT_SECRET" \
    -d username="$1" -d password="$DEMO_USER_PASSWORD" |
    sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p'
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

expect 401 "GET /api/me không có token"             "$GW/api/me"
expect 401 "GET /api/me với token sai chữ ký"       -H "Authorization: Bearer ${sv}x" "$GW/api/me"
expect 200 "GET /api/me với token sinhvien"         -H "Authorization: Bearer $sv" "$GW/api/me"
expect 403 "GET /api/data/stats với token sinhvien" -H "Authorization: Bearer $sv" "$GW/api/data/stats"
expect 200 "GET /api/me với token truongphong"      -H "Authorization: Bearer $tp" "$GW/api/me"
expect 401 "GET /api/workflow không có token"         "$GW/api/workflow/repository/process-definitions"
expect 200 "GET /api/workflow với token sinhvien"     -H "Authorization: Bearer $sv" "$GW/api/workflow/repository/process-definitions"

[ "$failed" -eq 0 ] || { echo "$failed kiểm tra không đạt"; exit 1; }

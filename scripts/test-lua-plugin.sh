#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0
#
# Cài plugin dxlab-roles vào một APISIX chạy riêng, theo đúng các bước của
# docs/build-from-source.md, rồi kiểm tra 401 / 403 / 200. Không cần stack, Keycloak hay .env:
# token được ký bằng khoá RSA tạm, APISIX kiểm chữ ký bằng public key tương ứng.
#
# APISIX ở đây là image chính thức, nhưng plugin được chép vào như với một bản cài sẵn,
# không mount thư mục của repo. APISIX_IMAGE đổi được phiên bản.
set -euo pipefail
cd "$(dirname "$0")/.."

IMAGE=${APISIX_IMAGE:-apache/apisix:3.19.0-debian}
PORT=${LUA_TEST_PORT:-9480}
NAME=dxlab-lua-test-$$
WORK=$(mktemp -d)
trap 'docker rm -f "$NAME" >/dev/null 2>&1 || true; rm -rf "$WORK"' EXIT

openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out "$WORK/key.pem" 2>/dev/null
openssl pkey -in "$WORK/key.pem" -pubout -out "$WORK/pub.pem"
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out "$WORK/other.pem" 2>/dev/null
ISSUER="http://127.0.0.1:9080/test"

# Bước 2 và 3 trong tài liệu: extra_lua_path và tên plugin trong config.yaml
cat > "$WORK/config.yaml" <<EOF
deployment:
  role: data_plane
  role_data_plane:
    config_provider: yaml
apisix:
  extra_lua_path: /opt/dxlab/?.lua
  enable_admin: false
plugins:
  - openid-connect
  - dxlab-roles
  - mocking
stream_plugins:
  - ip-restriction
EOF

# Route /check bật openid-connect rồi dxlab-roles, chỉ ROLE_ADMIN đi qua.
# Discovery do chính APISIX trả để không cần Keycloak.
{
  echo "routes:"
  echo "  - uri: /test/.well-known/openid-configuration"
  echo "    plugins:"
  echo "      mocking:"
  echo "        content_type: application/json"
  echo "        response_example: '{\"issuer\":\"$ISSUER\",\"jwks_uri\":\"$ISSUER/jwks\"}'"
  echo "    upstream: { type: roundrobin, nodes: { \"127.0.0.1:1\": 1 } }"
  echo "  - uri: /check"
  echo "    plugins:"
  echo "      openid-connect:"
  echo "        client_id: lua-test"
  echo "        discovery: $ISSUER/.well-known/openid-configuration"
  echo "        bearer_only: true"
  echo "        set_userinfo_header: true"
  echo "        token_signing_alg_values_expected: RS256"
  echo "        public_key: |"
  sed 's/^/          /' "$WORK/pub.pem"
  echo "      dxlab-roles:"
  echo "        roles: [ROLE_ADMIN]"
  echo "      mocking:"
  echo "        response_status: 200"
  echo "        response_example: ok"
  echo "    upstream: { type: roundrobin, nodes: { \"127.0.0.1:1\": 1 } }"
  echo "#END"
} > "$WORK/apisix.yaml"

docker create --name "$NAME" -p "127.0.0.1:$PORT:9080" "$IMAGE" >/dev/null
docker cp "$WORK/config.yaml" "$NAME:/usr/local/apisix/conf/config.yaml"
docker cp "$WORK/apisix.yaml" "$NAME:/usr/local/apisix/conf/apisix.yaml"
# Bước 1 trong tài liệu: chép plugin thành /opt/dxlab/apisix/plugins/dxlab-roles.lua
# (/opt/dxlab chưa có nên docker cp tạo nó với nội dung của core/gateway/plugins)
docker cp core/gateway/plugins "$NAME:/opt/dxlab"
docker start "$NAME" >/dev/null

for _ in $(seq 1 30); do
  curl -fsS -o /dev/null "http://127.0.0.1:$PORT/test/.well-known/openid-configuration" 2>/dev/null && break
  sleep 1
done

b64url() { openssl base64 -A | tr '+/' '-_' | tr -d '='; }
jwt() { # khoá, danh sách vai trò dạng JSON
  local now header payload
  now=$(date +%s)
  header=$(printf '{"alg":"RS256","typ":"JWT"}' | b64url)
  payload=$(printf '{"iss":"%s","sub":"lua-test","preferred_username":"lua-test","iat":%d,"exp":%d,"realm_access":{"roles":%s}}' \
    "$ISSUER" "$now" "$((now + 300))" "$2" | b64url)
  printf '%s.%s.%s' "$header" "$payload" \
    "$(printf '%s.%s' "$header" "$payload" | openssl dgst -sha256 -sign "$1" -binary | b64url)"
}

fail=0
expect() { # mã mong đợi, mô tả, tham số curl
  local want=$1 desc=$2 got
  shift 2
  got=$(curl -s -o /dev/null -w '%{http_code}' "$@" "http://127.0.0.1:$PORT/check")
  if [ "$got" = "$want" ]; then echo "PASS  $desc ($got)"; else echo "FAIL  $desc: $got, cần $want"; fail=1; fi
}

forged=$(printf '{"sub":"x","realm_access":{"roles":["ROLE_ADMIN"]}}' | openssl base64 -A)
expect 401 "không có token"
expect 401 "X-Userinfo tự gửi, không có token" -H "X-Userinfo: $forged"
expect 401 "token ký bằng khoá khác" -H "Authorization: Bearer $(jwt "$WORK/other.pem" '["ROLE_ADMIN"]')"
expect 403 "token đúng, sai vai trò" -H "Authorization: Bearer $(jwt "$WORK/key.pem" '["ROLE_STUDENT"]')"
expect 200 "token đúng, đúng vai trò" -H "Authorization: Bearer $(jwt "$WORK/key.pem" '["ROLE_STUDENT","ROLE_ADMIN"]')"

if [ "$fail" -ne 0 ]; then
  docker logs "$NAME" 2>&1 | tail -20
  exit 1
fi

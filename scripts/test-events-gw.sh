#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0
#
# Stream sự kiện qua /gw của app (đường trình duyệt dùng, #123): đăng nhập bằng phiên thật,
# mở /gw/api/data/events/stream với Accept-Encoding br, gzip, rồi gửi một phiếu. Sự kiện phải
# tới ngay (không bị gom hay nén) và response không có Content-Encoding.
# Cần profile integration (NATS). Chạy trong `make smoke-assets`.

set -euo pipefail

cd "$(dirname "$0")/.."
set -a
# shellcheck disable=SC1091
. ./.env
set +a
DEMO_USER_PASSWORD=$(printf '%s' "$DEMO_USER_PASSWORD" | tr -d '\r')

APP="http://localhost:${APP_PORT:-3000}"
WAIT=8
files=()
pid=""
cleanup() { [ -n "$pid" ] && kill "$pid" 2>/dev/null; rm -f "${files[@]}"; }
trap cleanup EXIT

login() {
  local jar kc_url form back
  jar=$(mktemp); files+=("$jar")
  kc_url=$(curl -s -c "$jar" -o /dev/null -w '%{redirect_url}' "$APP/auth/login")
  form=$(curl -s -b "$jar" -c "$jar" "$kc_url" | grep -o 'action="[^"]*"' | head -n 1 | sed 's/^action="//; s/"$//; s/&amp;/\&/g')
  back=$(curl -s -b "$jar" -c "$jar" -o /dev/null -w '%{redirect_url}' -X POST "$form" \
    --data-urlencode "username=$1" --data-urlencode "password=$DEMO_USER_PASSWORD")
  curl -s -b "$jar" -c "$jar" -o /dev/null "$back"
  printf '%s' "$jar"
}

sv=$(login sinhvien)
tp=$(login truongphong)
out=$(mktemp); hdr=$(mktemp); files+=("$out" "$hdr")

# -N: không đệm phía curl, để đo đúng thời điểm sự kiện tới
curl -sN -b "$tp" -H 'Accept: text/event-stream' -H 'Accept-Encoding: br, gzip' -D "$hdr" \
  "$APP/gw/api/data/events/stream" >"$out" &
pid=$!
for _ in $(seq 20); do grep -q 'connected' "$out" 2>/dev/null && break; sleep 0.25; done
if ! grep -q 'connected' "$out"; then
  echo "FAIL       events qua /gw: stream không mở được ($(head -n 1 "$hdr" | tr -d '\r'))"
  exit 1
fi

if grep -qi '^content-encoding:' "$hdr"; then
  echo "FAIL       events qua /gw: stream bị nén ($(grep -i '^content-encoding:' "$hdr" | tr -d '\r'))"
  exit 1
fi
echo "OK         events qua /gw: stream mở, không có Content-Encoding"

gw() {
  curl -s -b "$1" -X "$2" -H 'Content-Type: application/json' --data "${4:-{\}}" "$APP/gw/api/data$3"
}
title="Events gw smoke: máy chiếu C401 $(date +%s)"
id=$(gw "$sv" POST /tickets "{\"title\":\"$title\",\"description\":\"Không lên hình\",\"category\":\"HARDWARE\",\"priority\":\"MEDIUM\",\"location_id\":6}" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
sent=$(date +%s.%N)
gw "$sv" POST "/tickets/$id/actions/submit" >/dev/null

got=""
for _ in $(seq $((WAIT * 10))); do
  if grep -q "$id" "$out"; then got=$(date +%s.%N); break; fi
  sleep 0.1
done
if [ -z "$got" ]; then
  echo "FAIL       events qua /gw: không nhận được sự kiện của phiếu $id trong ${WAIT} giây (bị gom?)"
  exit 1
fi
echo "OK         events qua /gw: nhận sự kiện SUBMITTED sau $(python3 -c "print(round($got - $sent, 2))") giây"

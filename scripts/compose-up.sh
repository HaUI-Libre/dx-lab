#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0
#
# Dùng cho `make up` và `make demo`: dựng lại image của đội từ mã nguồn hiện tại rồi
# khởi động. Không có --build thì sau `git pull` Compose vẫn chạy image cũ đã có trên
# máy (ví dụ giao diện cũ). Image không đổi thì Docker dùng cache, chỉ mất vài giây.
#   scripts/compose-up.sh [tham số docker compose, ví dụ --profile integration]
set -euo pipefail
cd "$(dirname "$0")/.."

before=$(docker compose "$@" ps -q | sort)
docker compose "$@" up -d --build --wait
after=$(docker compose "$@" ps -q | sort)

# Container được tạo lại nhận IP mới, nhưng APISIX còn giữ IP cũ trong bộ nhớ đệm DNS
# và trả 502. Khởi động lại APISIX khi có container đổi, rồi chờ nó healthy.
if [ -n "$before" ] && [ "$before" != "$after" ]; then
  echo "Có container được tạo lại, khởi động lại APISIX để nhận địa chỉ mới"
  docker compose "$@" restart apisix
  docker compose "$@" up -d --wait apisix
fi

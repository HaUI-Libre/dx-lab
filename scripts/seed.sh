#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0
#
# Nạp dữ liệu mẫu 3 cơ sở HaUI vào PostgreSQL (dxdata) và Snipe-IT.
# Dùng: `make seed` hoặc `./scripts/seed.sh`

set -euo pipefail

cd "$(dirname "$0")/.."

if command -v python3 >/dev/null 2>&1; then
  exec python3 scripts/seed.py "$@"
elif command -v python >/dev/null 2>&1; then
  exec python scripts/seed.py "$@"
elif command -v py >/dev/null 2>&1; then
  exec py scripts/seed.py "$@"
else
  echo "[-] Không tìm thấy Python để chạy scripts/seed.py" >&2
  exit 1
fi

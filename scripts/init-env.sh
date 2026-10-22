#!/bin/sh
# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0
#
# Tạo .env từ .env.example, thay mọi giá trị "changeme" bằng chuỗi ngẫu nhiên.
# DEMO_USER_PASSWORD giữ nguyên để người chạy demo biết mật khẩu tài khoản demo.
# Không ghi đè .env đã có. Dùng: `make env`.

set -eu

cd "$(dirname "$0")/.."
if [ -f .env ]; then
  echo ".env đã có, không ghi đè"
  exit 0
fi

random() {
  od -An -N24 -tx1 /dev/urandom | tr -d ' \n'
}

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in
    DEMO_USER_PASSWORD=*) printf '%s\n' "$line" ;;
    *=changeme*) printf '%s=%s\n' "${line%%=*}" "$(random)" ;;
    *) printf '%s\n' "$line" ;;
  esac
done < .env.example > "$tmp"
mv "$tmp" .env
trap - EXIT
echo "Đã tạo .env với khoá ngẫu nhiên; mật khẩu tài khoản demo là DEMO_USER_PASSWORD trong .env"

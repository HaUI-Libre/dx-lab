#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0
#
# Role chỉ đọc số liệu cho postgres_exporter (#78). pg_monitor xem được thống kê của
# mọi database nhưng không đọc dữ liệu bảng, nên exporter không cần tài khoản superuser.

set -euo pipefail

if [ -z "${MONITOR_DB_PASSWORD:-}" ]; then
  echo "Bỏ qua tạo role dxmonitor: chưa đặt MONITOR_DB_PASSWORD"
  exit 0
fi

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
     -v password="$MONITOR_DB_PASSWORD" <<'SQL'
SELECT format('CREATE ROLE dxmonitor LOGIN PASSWORD %L', :'password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'dxmonitor') \gexec
GRANT pg_monitor TO dxmonitor;
SQL

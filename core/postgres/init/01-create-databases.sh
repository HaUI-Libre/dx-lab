#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0
#
# Tạo database và tài khoản riêng cho từng dịch vụ (Keycloak, Flowable, Data API).
# Image postgres chỉ chạy script này ở lần khởi tạo đầu tiên, khi volume còn trống.
# Muốn chạy lại: `docker compose down -v` (XÓA toàn bộ dữ liệu) rồi `make up`.

set -euo pipefail

create_db() {
  local name="$1" password="$2"
  echo "Tạo database và user: $name"
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
       -v name="$name" -v password="$password" <<'SQL'
SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'name', :'password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'name') \gexec
SELECT format('CREATE DATABASE %I OWNER %I', :'name', :'name')
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = :'name') \gexec
SELECT format('REVOKE ALL ON DATABASE %I FROM PUBLIC', :'name') \gexec
SQL
}

create_db keycloak "$KEYCLOAK_DB_PASSWORD"
create_db flowable "$FLOWABLE_DB_PASSWORD"
create_db dxdata "$DATA_DB_PASSWORD"

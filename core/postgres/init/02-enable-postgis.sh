#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0
#
# Bật PostGIS trên dxdata cho định tuyến theo cơ sở (#76, #79). Thư mục init được
# mount đè lên /docker-entrypoint-initdb.d nên script 10_postgis.sh của image không
# chạy; extension chỉ bật ở database cần dùng. PostGIS không phải extension "trusted",
# nên phải tạo bằng superuser ở đây thay vì từ migration của Data API.

set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname dxdata \
     -c 'CREATE EXTENSION IF NOT EXISTS postgis'

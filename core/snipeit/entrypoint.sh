#!/bin/bash
# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

set -e

KEY_DIR="/var/lib/snipeit/keys"
KEY_FILE="${KEY_DIR}/snipeit_app_key"

mkdir -p "$KEY_DIR"

if [ -z "$APP_KEY" ] || [ "$APP_KEY" = "changeme" ]; then
    if [ -f "$KEY_FILE" ] && [ -s "$KEY_FILE" ]; then
        echo "[Snipe-IT Entrypoint] Đọc APP_KEY đã lưu từ ${KEY_FILE}..."
        export APP_KEY=$(cat "$KEY_FILE" | tr -d '\r\n')
    else
        echo "[Snipe-IT Entrypoint] Khởi tạo và lưu APP_KEY mới..."
        GENERATED_KEY=$(php /var/www/html/artisan key:generate --show --no-ansi | tr -d '\r\n')
        echo "$GENERATED_KEY" > "$KEY_FILE"
        chmod 600 "$KEY_FILE"
        chown docker:root "$KEY_FILE"
        export APP_KEY="$GENERATED_KEY"
    fi
fi

echo "[Snipe-IT Entrypoint] Đang kiểm tra kết nối tới MariaDB..."
until (exec 3<>/dev/tcp/mariadb/3306) 2>/dev/null; do
    echo "[Snipe-IT Entrypoint] Đợi MariaDB mở cổng 3306..."
    sleep 2
done
echo "[Snipe-IT Entrypoint] Đã kết nối được MariaDB:3306."

# Chạy tiến trình khởi tạo DX-Lab và nạp dữ liệu mẫu ngầm trong container
/opt/dxlab/init.sh &

# Chuyển quyền điều khiển cho tiến trình khởi động chính thức của Snipe-IT
exec /startup.sh

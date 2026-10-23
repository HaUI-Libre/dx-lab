#!/bin/bash
# SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
# SPDX-License-Identifier: Apache-2.0

set -e

echo "[Snipe-IT Init] Đang đợi dịch vụ web Snipe-IT sẵn sàng..."
until curl -s -f http://127.0.0.1/health >/dev/null 2>&1 || curl -s -I http://127.0.0.1/ | grep -q "HTTP/" 2>/dev/null; do
    sleep 2
done
echo "[Snipe-IT Init] Dịch vụ web Snipe-IT đã phản hồi."

# Kiểm tra trạng thái cấu hình (Setting::setupCompleted())
STATUS=$(php /opt/dxlab/check_setup.php 2>/dev/null || echo "PENDING")

if [ "$STATUS" != "COMPLETED" ]; then
    echo "[Snipe-IT Init] Tạo tài khoản admin khởi tạo..."
    php /var/www/html/artisan snipeit:create-admin \
        --first_name="Admin" \
        --last_name="DX-Lab" \
        --email="admin@dxlab.local" \
        --username="${SNIPEIT_ADMIN_USER:-admin}" \
        --password="${SNIPEIT_ADMIN_PASSWORD:-changeme}" || true

    echo "[Snipe-IT Init] Nạp dữ liệu mẫu ban đầu..."
    php /opt/dxlab/seed.php /opt/dxlab-data/snipeit_seed.json
fi

# Khởi tạo Passport OAuth keys nếu chưa có
if [ ! -f /var/lib/snipeit/keys/oauth-private.key ]; then
    echo "[Snipe-IT Init] Khởi tạo Passport OAuth keys..."
    php /var/www/html/artisan passport:keys --force
fi

# Đảm bảo có personal access client cho API token
echo "[Snipe-IT Init] Đảm bảo Passport personal access client tồn tại..."
php /var/www/html/artisan passport:client --personal --no-interaction --name="DX-Lab Integration" || true

# Đảm bảo thư mục /token tồn tại
mkdir -p /token

# Sinh hoặc đọc API Token trên volume snipeit-token
TOKEN_FILE="/token/snipeit_api_token"
if [ ! -f "$TOKEN_FILE" ] || [ ! -s "$TOKEN_FILE" ]; then
    echo "[Snipe-IT Init] Khởi tạo tài khoản và API Token riêng cho dịch vụ tích hợp..."
    php /opt/dxlab/create_integration_token.php
    chmod 0600 "$TOKEN_FILE"
    chown docker:root "$TOKEN_FILE"
fi
php /opt/dxlab/sync_integration_permissions.php

# Thiết lập quyền sở hữu để tránh lỗi supervisord run_schedule
chown -R docker:root /var/www/html/storage /var/lib/snipeit /token
chmod 0640 "$TOKEN_FILE"

echo "============================================================"
echo "[Snipe-IT Init] Snipe-IT đã sẵn sàng cho tích hợp!"
echo "[Snipe-IT Init] API Token lưu tại: ${TOKEN_FILE}"
echo "============================================================"

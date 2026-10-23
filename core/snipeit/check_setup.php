<?php
// SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
// SPDX-License-Identifier: Apache-2.0

try {
    require_once '/var/www/html/vendor/autoload.php';
    $app = require_once '/var/www/html/bootstrap/app.php';
    $app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

    if (\App\Models\Setting::setupCompleted()) {
        echo "COMPLETED\n";
        exit(0);
    }
} catch (\Throwable $e) {
    // Database hoặc bảng settings chưa sẵn sàng
}

echo "PENDING\n";

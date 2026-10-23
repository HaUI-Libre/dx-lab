<?php
// SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
// SPDX-License-Identifier: Apache-2.0

require_once '/var/www/html/vendor/autoload.php';
$app = require_once '/var/www/html/bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

use App\Models\User;

$user = User::where('username', 'dxlab-integration')->first();
if (!$user) {
    fwrite(STDERR, "[Snipe-IT Init] Tài khoản tích hợp chưa tồn tại.\n");
    exit(1);
}
$raw = $user->permissions;
$permissions = is_array($raw) ? $raw : (json_decode($raw ?: '{}', true) ?: []);
$permissions['users.view'] = 1;
$user->permissions = json_encode($permissions);
$user->save();

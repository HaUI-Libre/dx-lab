<?php
// SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
// SPDX-License-Identifier: Apache-2.0

require_once '/var/www/html/vendor/autoload.php';
$app = require_once '/var/www/html/bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

use App\Models\User;
use Illuminate\Support\Str;

$username = 'dxlab-integration';
$user = User::firstOrNew(['username' => $username]);
$user->first_name = 'DX-Lab';
$user->last_name = 'Integration';
$user->email = 'integration@dxlab.local';
$user->activated = 1;
if (!$user->exists) {
    $user->password = bcrypt(Str::random(32));
}
$user->permissions = json_encode([
    'assets.view' => 1,
    'assets.edit' => 1,
    'assets.checkin' => 1,
    'assets.checkout' => 1,
    'users.view' => 1,
    'locations.view' => 1,
    'statuslabels.view' => 1,
]);
$user->save();

$tokenResult = $user->createToken('DX-Lab Integration');
$tokenString = $tokenResult->accessToken;

$tokenFile = '/token/snipeit_api_token';
if (!is_dir(dirname($tokenFile))) {
    mkdir(dirname($tokenFile), 0755, true);
}
file_put_contents($tokenFile, $tokenString . "\n");
chmod($tokenFile, 0600);
echo "[Snipe-IT Init] Đã tạo thành công API Token cho user '{$user->username}' (ID: {$user->id})\n";

<?php
// SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
// SPDX-License-Identifier: Apache-2.0

require_once '/var/www/html/vendor/autoload.php';
$app = require_once '/var/www/html/bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

use App\Models\Setting;
use App\Models\Statuslabel;
use App\Models\Category;
use App\Models\Manufacturer;
use App\Models\AssetModel;
use App\Models\Location;
use App\Models\User;
use App\Models\Asset;
use Illuminate\Support\Str;

echo "[Snipe-IT Seed] 1. Cấu hình thiết lập hệ thống (Setting)...\n";
$s = Setting::first() ?? new Setting;
$s->site_name = 'DX-Lab Snipe-IT';
$s->default_currency = 'VND';
$s->brand = 1;
$s->email_domain = 'dxlab.local';
$s->email_format = 'firstname.lastname';
$s->username_format = 'username';
$s->locale = 'vi';
$s->pwd_secure_min = 8;
$s->block_api_user_agents = 0;
$s->save();

$jsonPath = $argv[1] ?? '/opt/dxlab-data/snipeit_seed.json';
if (!file_exists($jsonPath)) {
    fwrite(STDERR, "[Snipe-IT Seed] Lỗi: Tệp dữ liệu mẫu không tồn tại tại $jsonPath\n");
    exit(1);
}

$data = json_decode(file_get_contents($jsonPath), true);
if (!$data) {
    fwrite(STDERR, "[Snipe-IT Seed] Lỗi: Không thể giải mã JSON từ $jsonPath\n");
    exit(1);
}

echo "[Snipe-IT Seed] 2. Nạp nhãn trạng thái tài sản (Status Labels)...\n";
Statuslabel::whereIn('name', ['Pending', 'Ready to Deploy', 'Archived'])->forceDelete();
foreach ($data['status_labels'] as $item) {
    $label = Statuslabel::firstOrNew(['name' => $item['name']]);
    $types = Statuslabel::getStatuslabelTypesForDB($item['type']);
    $label->deployable = $types['deployable'];
    $label->pending = $types['pending'];
    $label->archived = $types['archived'];
    $label->notes = $item['notes'] ?? null;
    $label->show_in_nav = !empty($item['show_in_nav']) ? 1 : 0;
    $label->default_label = !empty($item['default_label']) ? 1 : 0;
    if (!$label->save()) {
        fwrite(STDERR, "[Snipe-IT Seed] Lỗi lưu Statuslabel '{$item['name']}': " . json_encode($label->getErrors()) . "\n");
    }
}

echo "[Snipe-IT Seed] 3. Nạp danh mục thiết bị (Categories)...\n";
foreach ($data['categories'] as $item) {
    $cat = Category::firstOrNew(['name' => $item['name']]);
    $cat->category_type = $item['category_type'];
    $cat->use_default_eula = !empty($item['use_default_eula']) ? 1 : 0;
    $cat->require_acceptance = !empty($item['require_acceptance']) ? 1 : 0;
    $cat->save();
}

echo "[Snipe-IT Seed] 4. Nạp nhà sản xuất (Manufacturers)...\n";
foreach ($data['manufacturers'] as $item) {
    $mfg = Manufacturer::firstOrNew(['name' => $item['name']]);
    $mfg->save();
}

echo "[Snipe-IT Seed] 5. Nạp loại / mẫu thiết bị (Models)...\n";
foreach ($data['models'] as $item) {
    $mfg = Manufacturer::where('name', $item['manufacturer'])->first();
    $cat = Category::where('name', $item['category'])->first();
    $model = AssetModel::firstOrNew(['name' => $item['name']]);
    $model->model_number = $item['model_number'];
    $model->manufacturer_id = $mfg ? $mfg->id : 1;
    $model->category_id = $cat ? $cat->id : 1;
    $model->save();
}

echo "[Snipe-IT Seed] 6. Nạp cây vị trí 3 cơ sở (Locations)...\n";
foreach ($data['locations'] as $item) {
    $loc = Location::firstOrNew(['id' => $item['id']]);
    $loc->name = $item['name'];
    $loc->parent_id = $item['parent_id'] ?? null;
    $loc->address = $item['address'] ?? null;
    $loc->city = $item['city'] ?? null;
    $loc->state = $item['state'] ?? null;
    $loc->country = $item['country'] ?? 'VN';
    $loc->currency = 'VND';
    $loc->save();
}

echo "[Snipe-IT Seed] 7. Nạp tài khoản người dùng (Users)...\n";
$demoPassword = getenv('DEMO_USER_PASSWORD') ?: 'changeme';
$adminUser = getenv('SNIPEIT_ADMIN_USER') ?: 'admin';
foreach ($data['users'] as $item) {
    $user = User::firstOrNew(['username' => $item['username']]);
    $user->first_name = $item['first_name'];
    $user->last_name = $item['last_name'];
    $user->email = $item['email'];
    $user->employee_num = $item['employee_num'] ?? null;
    $user->location_id = $item['location_id'] ?? null;
    $user->notes = $item['notes'] ?? null;
    $user->password = bcrypt($demoPassword);
    $user->activated = 1;
    if ($item['username'] === 'quantri' || $item['username'] === $adminUser) {
        $user->permissions = '{"admin":1,"user":1,"superuser":1,"reports":1}';
    }
    $user->save();
}

// Tài khoản riêng cho dịch vụ tích hợp DX-Lab (#71)
$integrationUser = User::firstOrNew(['username' => 'dxlab-integration']);
$integrationUser->first_name = 'DX-Lab';
$integrationUser->last_name = 'Integration';
$integrationUser->email = 'integration@dxlab.local';
$integrationUser->activated = 1;
if (!$integrationUser->exists) {
    $integrationUser->password = bcrypt(Str::random(32));
}
$integrationUser->permissions = json_encode([
    'assets.view' => 1,
    'assets.edit' => 1,
    'assets.checkin' => 1,
    'assets.checkout' => 1,
    'users.view' => 1,
    'locations.view' => 1,
    'statuslabels.view' => 1,
]);
$integrationUser->save();

echo "[Snipe-IT Seed] 8. Nạp tài sản mẫu (Assets)...\n";
foreach ($data['assets'] as $item) {
    $model = AssetModel::where('name', $item['model'])->first();
    $status = Statuslabel::where('name', $item['status'])->first();
    $assignedUser = !empty($item['assigned_to_username']) ? User::where('username', $item['assigned_to_username'])->first() : null;

    $asset = Asset::firstOrNew(['asset_tag' => $item['asset_tag']]);
    $asset->name = $item['name'];
    $asset->model_id = $model ? $model->id : 1;
    $asset->status_id = $status ? $status->id : 1;
    $asset->location_id = $item['location_id'] ?? null;
    $asset->rtd_location_id = $item['location_id'] ?? null;
    $asset->serial = $item['serial'] ?? null;
    $asset->purchase_date = $item['purchase_date'] ?? null;
    $asset->notes = $item['notes'] ?? null;
    if ($assignedUser) {
        $asset->assigned_to = $assignedUser->id;
        $asset->assigned_type = User::class;
    } else {
        $asset->assigned_to = null;
        $asset->assigned_type = null;
    }
    $asset->save();
}

echo "[Snipe-IT Seed] Hoàn tất nạp dữ liệu mẫu Snipe-IT thành công!\n";

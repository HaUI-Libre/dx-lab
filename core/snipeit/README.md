<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Snipe-IT và MariaDB (Profile: integration)

Thư mục này chứa cấu hình và kịch bản khởi tạo dịch vụ giả lập hệ thống quản lý tài sản của khách hàng bằng **Snipe-IT** và **MariaDB**.

## 1. Vai trò trong kiến trúc

- **Giả lập hệ thống có sẵn của khách hàng**: Trong nghiệp vụ DX-Helpdesk, tài sản CNTT (máy tính, máy in, máy chiếu, thiết bị mạng) đã được quản trị trước đó trên hệ thống của đơn vị đào tạo / doanh nghiệp. DX-Lab tích hợp với hệ thống này để lấy danh sách thiết bị của sinh viên/giảng viên và đồng bộ trạng thái khi báo hỏng hoặc sửa chữa xong.
- **Nằm ngoài DX-OS Open-Core**: Snipe-IT và MariaDB được tách biệt vào profile `integration` trong `docker-compose.yml`, không ảnh hưởng tới lõi mặc định (`make up`).
- **Ranh giới kiến trúc và giấy phép (ADR-06)**:
  - Snipe-IT phát hành theo giấy phép **AGPL-3.0**, MariaDB theo **GPL-2.0**.
  - **Không chỉnh sửa mã nguồn Snipe-IT** trong repo; chạy nguyên bản image container chính thức `snipe/snipe-it:v8.8.0` và `mariadb:11.4.7`.
  - **Không cho bất kỳ dịch vụ nào của DX-Lab truy cập trực tiếp cơ sở dữ liệu MariaDB**; MariaDB không mở cổng ra máy host hay các mạng khác.
  - Toàn bộ giao tiếp giữa DX-Lab và Snipe-IT chỉ thực hiện qua giao diện **REST API `/api/v1`** có xác thực API Bearer Token thông qua dịch vụ tích hợp tài sản (`asset-sync`).

## 2. Cấu trúc thư mục

- `entrypoint.sh`: Điểm khởi chạy của container Snipe-IT, tự động quản lý sinh/lưu `APP_KEY`, kích hoạt tiến trình khởi tạo ngầm và chuyển quyền cho `/startup.sh` chính thức.
- `init.sh`: Kịch bản chờ Snipe-IT sẵn sàng, tạo tài khoản quản trị ban đầu, kích hoạt OAuth Passport keys, gọi `seed.php` và sinh API Token.
- `create_integration_token.php`: Khởi tạo tài khoản `dxlab-integration` và phát API Token lưu vào volume `snipeit-token`.
- `seed.php`: Kịch bản PHP Eloquent nạp dữ liệu mẫu ban đầu từ `data/samples/snipeit_seed.json`.
- `check_setup.php`: Kiểm tra xem hệ thống đã hoàn thành cấu hình ban đầu (`Setting::setupCompleted()`) chưa.

## 3. Khởi động và sử dụng

### 3.1. Cấu hình biến môi trường

Trong tệp `.env`, khai báo các biến:

```dotenv
SNIPEIT_PORT=8081
SNIPEIT_APP_KEY=changeme
MARIADB_ROOT_PASSWORD=changeme
SNIPEIT_DB_DATABASE=snipeit
SNIPEIT_DB_USERNAME=snipeit
SNIPEIT_DB_PASSWORD=changeme
SNIPEIT_ADMIN_USER=admin
SNIPEIT_ADMIN_PASSWORD=changeme
```

- **Quản lý APP_KEY**: Nếu `SNIPEIT_APP_KEY=changeme` hoặc để trống, `entrypoint.sh` sẽ tự động sinh khóa bằng `php artisan key:generate --show` ở lần chạy đầu tiên, lưu vào volume `snipeit-data` (`/var/lib/snipeit/keys/snipeit_app_key`), và các lần chạy sau sẽ đọc lại khóa này nhằm đảm bảo tính toàn vẹn dữ liệu mã hóa.

### 3.2. Khởi chạy với profile integration

Khởi động các dịch vụ lõi cùng Snipe-IT và MariaDB:

```bash
docker compose --profile integration up -d
```

Hoặc chỉ khởi động riêng Snipe-IT và MariaDB:

```bash
docker compose --profile integration up -d mariadb snipeit
```

### 3.3. Dữ liệu mẫu (Seed Data)

Kịch bản `seed.php` tự động nạp các mục sau từ `data/samples/snipeit_seed.json`:
1. **Thiết lập hệ thống**: Tên hệ thống `DX-Lab Snipe-IT`, tiền tệ `VND`, giao diện tiếng Việt (`vi`), không chặn API client.
2. **Nhãn trạng thái (4 Status Labels)**: `Sẵn sàng` (Deployable), `Đang sửa chữa` (Pending), `Đang bảo trì` (Undeployable), `Thanh lý` (Archived).
3. **Danh mục (Categories)**: `Máy tính trạm`, `Máy tính xách tay`, `Thiết bị mạng`, `Thiết bị hiển thị & Ngoại vi`.
4. **Nhà sản xuất (Manufacturers)**: `Dell Inc.`, `HP Inc.`, `Lenovo`, `Cisco Systems`, `Panasonic`.
5. **Mẫu thiết bị (Models)**: `Dell OptiPlex 7090`, `HP EliteDesk 800 G6`, `Lenovo ThinkCentre M70q`, `Dell Latitude 5420`, `Cisco Catalyst 2960-X`, `Panasonic PT-LB386`.
6. **Cây vị trí 3 cơ sở (20 Locations)**:
   - Cơ sở 1 - Trụ sở chính (Hà Nội): Tòa C, Tòa A10, cùng các phòng lab/thực hành C301, C302, C401, C402, A10-502.
   - Cơ sở 2 (Tây Tựu): Tòa B1, Tòa B2, cùng các phòng thực hành/lab B1-201, B1-202, B2-301.
   - Cơ sở 3 (Phủ Lý, Hà Nam): Tòa H1, Tòa H2, cùng các phòng PM301, PM302, LAB205.
7. **Người dùng (Users)**: Các tài khoản sinh viên, kỹ thuật viên, quản lý lab và quản trị viên khớp với Keycloak.
8. **Tài khoản tích hợp API riêng (`dxlab-integration`)**: Không phải superuser, chỉ được phân quyền đọc/sửa tài sản (`assets.view`, `assets.edit`, `assets.checkin`, `assets.checkout`) và đọc vị trí (`locations.view`, `statuslabels.view`).
9. **Tài sản mẫu (Assets)**: 16 thiết bị CNTT mẫu có gắn thẻ `asset_tag` (VD: `HAUI-PC-0002`, `HAUI-CS1-PC01`, `HAUI-CS1-SW01`), gán vị trí phòng và người dùng phụ trách.

### 3.4. API Token và tích hợp (#72)

- Container Snipe-IT tự động sinh Personal Access Token cho tài khoản `dxlab-integration` và ghi vào tệp `/token/snipeit_api_token` trên volume `snipeit-token`. Tệp thuộc nhóm `root`, quyền `0640` để tiến trình asset-sync (UID 10001, GID 0) đọc được.
- **Dịch vụ tích hợp tài sản (#72)**: Dịch vụ `asset-sync` mount volume `snipeit-token` ở chế độ chỉ đọc (`:ro`) tại `/token` và đọc trực tiếp token từ `/token/snipeit_api_token` để xác thực với Snipe-IT REST API `/api/v1`. Hệ thống không lưu token vào tệp `.env`. Tài khoản này có thêm quyền `users.view` để tra đúng username của người đăng nhập; init cập nhật quyền này trên volume đã có.

Xem token trên máy host bằng lệnh:

```bash
make snipeit-token
# Hoặc:
docker compose --profile integration exec snipeit cat /token/snipeit_api_token
```

Kiểm tra kết nối REST API tới Snipe-IT bằng token:

```bash
TOKEN=$(make snipeit-token)
curl -s -H "Accept: application/json" \
     -H "Authorization: Bearer $TOKEN" \
     http://127.0.0.1:8081/api/v1/hardware | jq .
```

<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# core/identity – Keycloak

`realm-dxlab.json` được import tự động khi Keycloak khởi động (`--import-realm`).
Các giá trị `${...}` trong file được Keycloak thay bằng biến môi trường lấy từ `.env`,
nên file không chứa mật khẩu thật.

JSON không có cú pháp comment nên không đặt được header SPDX; giấy phép của
`realm-dxlab.json` ghi trong tệp đi kèm `realm-dxlab.json.license` theo chuẩn REUSE.

## Nội dung realm

| Thành phần | Giá trị |
|---|---|
| Realm | `${KEYCLOAK_REALM}` (mặc định `dxlab`) |
| Client OIDC | `${KEYCLOAK_CLIENT_ID}` (mặc định `dxlab-app`), confidential, PKCE S256, bật Direct Access Grants để lấy token bằng curl; redirect URI và web origin là `${APP_URL}` của ứng dụng Nuxt |
| Realm role | `ROLE_STUDENT`, `ROLE_TECHNICIAN`, `ROLE_LAB_MANAGER`, `ROLE_ADMIN` (theo M1.3) |

Tài khoản demo, mật khẩu chung là `DEMO_USER_PASSWORD`:

| Username | Vai trò | Cơ sở | UUID |
|---|---|---|---|
| `sinhvien` | `ROLE_STUDENT` | — | `e90585fa-96ac-5f81-87a3-f817cc6d4323` |
| `kythuatvien` | `ROLE_TECHNICIAN` | CS1 | `9f19d880-973b-592b-bdb3-a354ac11cd6a` |
| `truongphong` | `ROLE_LAB_MANAGER` | CS1 | `d8608553-a02a-50b8-b05f-6cfe42da7850` |
| `quantri` | `ROLE_ADMIN` | — | `7d3ff8eb-0b1b-55a6-9dcd-8197344c83e2` |
| `sinhvien_cs2` | `ROLE_STUDENT` | — | `2324827d-3d37-5241-997f-25b64722818d` |
| `kythuatvien_cs2` | `ROLE_TECHNICIAN` | CS2 | `18685db0-c1c9-5e08-97cd-fdd20f23f6ed` |
| `truongphong_cs2` | `ROLE_LAB_MANAGER` | CS2 | `8fe64e2b-4772-5d63-ad4d-f48698f6b58e` |
| `sinhvien_cs3` | `ROLE_STUDENT` | — | `a7e3965a-b5b0-5a1f-b755-8f0f9130895b` |
| `kythuatvien_cs3` | `ROLE_TECHNICIAN` | CS3 | `b8074364-5be8-55e6-9106-a68702cbde00` |
| `truongphong_cs3` | `ROLE_LAB_MANAGER` | CS3 | `58ab5e48-abac-5e8e-8336-feb7e3e18a9e` |

Admin console: http://localhost:8080/admin (tài khoản `KEYCLOAK_ADMIN`).

## Lấy token bằng curl

```bash
set -a; . ./.env; set +a
curl -s -X POST "http://localhost:8080/realms/$KEYCLOAK_REALM/protocol/openid-connect/token" \
  -d grant_type=password \
  -d client_id="$KEYCLOAK_CLIENT_ID" -d client_secret="$KEYCLOAK_CLIENT_SECRET" \
  -d username=sinhvien -d password="$DEMO_USER_PASSWORD"
```

Vai trò nằm trong claim `realm_access.roles`; kỹ thuật viên và quản lý còn có
claim chuỗi `co_so` trong access token. Client mapper lấy user attribute cùng tên.
UUID demo được ghim trong realm để dữ liệu seed (#84) tham chiếu cùng người dùng.
User profile Keycloak 26 khai báo `co_so` là thuộc tính đơn trị, chỉ admin sửa;
các thuộc tính hồ sơ chuẩn vẫn giữ trong cấu hình profile. Điều này ngăn người
dùng tự đổi cơ sở qua trang hồ sơ.

## Issuer

`KC_HOSTNAME` được ghim là `http://localhost:8080`, nên mọi token đều có
`iss=http://localhost:8080/realms/dxlab`, dù lấy từ trình duyệt hay từ container khác.
Các service trong mạng compose (APISIX, Data API) vẫn tải discovery và JWKS qua
`http://keycloak:8080` nhờ `KC_HOSTNAME_BACKCHANNEL_DYNAMIC`.

## Sửa realm

Keycloak chỉ import khi realm **chưa tồn tại**. Sau khi sửa `realm-dxlab.json`,
hãy kiểm thử import trên Compose project riêng trước. Ví dụ, dùng một bản sao
repo trong thư mục khác, `COMPOSE_PROJECT_NAME=dxlab-realm-check` và các cổng
host khác trong `.env` của bản sao rồi chạy `make up && make smoke`. Project riêng
có volume riêng; không dùng `down -v` trên project đang làm việc.

Để cập nhật realm đang tồn tại, cần thực hiện thay đổi tương ứng qua Keycloak
Admin API/console hoặc chủ động tái tạo **riêng** realm đó sau khi sao lưu. Có thể:

- Xóa realm `dxlab` trong admin console rồi `docker compose restart keycloak`;
  thao tác này xóa dữ liệu Keycloak của realm, chỉ thực hiện khi đã sao lưu.

Thay đổi làm trên admin console không tự ghi vào file. Muốn giữ lại thì sửa file
bằng tay, rồi kiểm tra lại bằng một trong hai cách trên.

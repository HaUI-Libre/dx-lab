<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# core/identity – Keycloak

`realm-dxlab.json` được import tự động khi Keycloak khởi động (`--import-realm`).
Các giá trị `${...}` trong file được Keycloak thay bằng biến môi trường lấy từ `.env`,
nên file không chứa mật khẩu thật.

## Nội dung realm

| Thành phần | Giá trị |
|---|---|
| Realm | `${KEYCLOAK_REALM}` (mặc định `dxlab`) |
| Client OIDC | `${KEYCLOAK_CLIENT_ID}` (mặc định `dxlab-app`), confidential, PKCE S256, bật Direct Access Grants để lấy token bằng curl |
| Realm role | `ROLE_STUDENT`, `ROLE_TECHNICIAN`, `ROLE_LAB_MANAGER`, `ROLE_ADMIN` (theo M1.3) |

Tài khoản demo, mật khẩu chung là `DEMO_USER_PASSWORD`:

| Username | Vai trò |
|---|---|
| `sinhvien` | `ROLE_STUDENT` |
| `kythuatvien` | `ROLE_TECHNICIAN` |
| `truongphong` | `ROLE_LAB_MANAGER` |
| `quantri` | `ROLE_ADMIN` |

Admin console: http://localhost:8080/admin (tài khoản `KEYCLOAK_ADMIN`).

## Lấy token bằng curl

```bash
set -a; . ./.env; set +a
curl -s -X POST "http://localhost:8080/realms/$KEYCLOAK_REALM/protocol/openid-connect/token" \
  -d grant_type=password \
  -d client_id="$KEYCLOAK_CLIENT_ID" -d client_secret="$KEYCLOAK_CLIENT_SECRET" \
  -d username=sinhvien -d password="$DEMO_USER_PASSWORD"
```

Vai trò nằm trong claim `realm_access.roles` của access token.

## Issuer

`KC_HOSTNAME` được ghim là `http://localhost:8080`, nên mọi token đều có
`iss=http://localhost:8080/realms/dxlab`, dù lấy từ trình duyệt hay từ container khác.
Các service trong mạng compose (APISIX, Data API) vẫn tải discovery và JWKS qua
`http://keycloak:8080` nhờ `KC_HOSTNAME_BACKCHANNEL_DYNAMIC`.

## Sửa realm

Keycloak chỉ import khi realm **chưa tồn tại**. Sau khi sửa `realm-dxlab.json`:

- Xóa realm `dxlab` trong admin console rồi `docker compose restart keycloak`, hoặc
- `docker compose down -v && make up` (**xóa toàn bộ dữ liệu**, kể cả các DB khác).

Thay đổi làm trên admin console không tự ghi vào file. Muốn giữ lại thì sửa file
bằng tay, rồi kiểm tra lại bằng một trong hai cách trên.

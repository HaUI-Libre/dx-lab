<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# app/ – DX-Helpdesk (Nuxt 4)

Giao diện H-P-D-I và ứng dụng DX-Helpdesk, chạy tại http://localhost:3000
(đổi bằng `APP_PORT` trong `.env`). Hiện có đăng nhập, đăng xuất SSO và trang
thông tin tài khoản (#24); các màn hình nghiệp vụ làm ở #26.

## Chạy

```bash
make up      # dựng image app từ mã nguồn lần đầu, rồi chạy cùng các service khác
make smoke   # có bước đăng nhập SSO qua app
```

Sau khi sửa mã trong `app/`, dựng lại image: `docker compose build app && make up`.

Phát triển có hot reload trên máy host (cần Node.js 24 LTS), trong khi các service
khác vẫn chạy bằng `make up`:

```bash
docker compose stop app
cd app && npm ci
NUXT_OIDC_CLIENT_SECRET=<KEYCLOAK_CLIENT_SECRET> \
NUXT_SESSION_PASSWORD=<APP_SESSION_PASSWORD> npm run dev
```

## Đăng nhập (mô hình BFF)

Client `dxlab-app` trong Keycloak là client confidential, có client secret, nên
trình duyệt không được giữ token. Server Nuxt làm thay:

1. `GET /auth/login`: tạo PKCE, `state`, `nonce`, chuyển sang trang đăng nhập Keycloak.
2. `GET /auth/callback`: đổi code lấy token qua `keycloak:8080` (mạng nội bộ). Token
   lưu trong bộ nhớ server, trình duyệt chỉ nhận cookie `dxlab_session` (httpOnly,
   SameSite=Lax, mã hoá bằng `APP_SESSION_PASSWORD`).
3. `/gw/api/**`: server gắn `Authorization: Bearer <access token>` rồi chuyển tiếp
   sang APISIX. Cookie của app không đi tiếp. Access token sắp hết hạn thì server tự
   làm mới bằng refresh token.
4. `POST /auth/logout`: xoá phiên ở app rồi chuyển sang Keycloak để kết thúc phiên SSO.

Mọi lời gọi API vẫn đi qua APISIX; gateway và dịch vụ phía sau tự kiểm tra token và
vai trò. App không gọi thẳng PostgreSQL, Flowable, SeaweedFS hay dịch vụ AI.

Trang chủ lấy tên, vai trò và cơ sở từ `GET /api/me` qua gateway. Claim `co_so` có
khi realm có thuộc tính cơ sở (#74); chưa có thì trang ghi "Chưa gán cơ sở".

## Cổng thông tin [H] (Portal tối giản - #25)

Không gian Con người số [H] tại `/portal`:
- **Hồ sơ cá nhân**: Tên, tài khoản, email, vai trò nghiệp vụ (4 vai trò: `ROLE_STUDENT`, `ROLE_TECHNICIAN`, `ROLE_LAB_MANAGER`, `ROLE_ADMIN`) và thuộc tính cơ sở làm việc (`co_so`: CS1, CS2, CS3), định danh OIDC `sub`.
- **Nhóm & Đơn vị**: Tổ kỹ thuật và quản lý phòng lab tại 3 cơ sở đào tạo HaUI (CS1 - Bắc Từ Liêm, CS2 - Tây Tựu, CS3 - Hà Nam), hotline, email hỗ trợ và phân định trách nhiệm luồng nghiệp vụ.
- **Tài liệu hướng dẫn**:
  - Tải lên (`PUT /gw/api/files/...`), xem trực tiếp (preview) và tải về qua `/api/files` của APISIX kết nối SeaweedFS (bucket `documents`).
  - Phân quyền tài liệu theo vai trò người dùng: sinh viên chỉ thấy tài liệu sinh viên và nội quy chung; kỹ thuật viên thấy tài liệu kỹ thuật; quản lý thấy tài liệu phân công & nghiệm thu; admin toàn quyền xem và vận hành.
  - API phục vụ giao diện: `GET /api/portal/documents`, `POST /api/portal/documents`, `GET /api/portal/groups`.

## Cấu hình

| Biến (`.env`) | Biến trong container | Ý nghĩa |
|---|---|---|
| `APP_PORT` | `NUXT_APP_URL` | Cổng của app; dùng chung cho redirect URI trong realm và CORS ở gateway |
| `APP_SESSION_PASSWORD` | `NUXT_SESSION_PASSWORD` | Khoá mã hoá cookie phiên, ít nhất 32 ký tự (`openssl rand -hex 32`) |
| `KEYCLOAK_CLIENT_ID`, `KEYCLOAK_CLIENT_SECRET` | `NUXT_OIDC_CLIENT_ID`, `NUXT_OIDC_CLIENT_SECRET` | Client OIDC |
| `KEYCLOAK_REALM` | `NUXT_OIDC_ISSUER_INTERNAL` | Địa chỉ Keycloak trong mạng compose |
| | `NUXT_GATEWAY_URL` | `http://apisix:9080` |

Đổi `APP_PORT` sau khi đã chạy lần đầu thì realm cũ vẫn giữ redirect URI cũ (realm
chỉ import một lần): xem mục "Sửa realm" trong `core/identity/README.md`.

## Giới hạn hiện tại

- Phiên lưu trong bộ nhớ: khởi động lại container `app` thì người dùng đăng nhập lại.
- HTTP thuần, đúng với Keycloak `start-dev`; chạy HTTPS thì cookie tự bật `Secure`
  khi `NUXT_APP_URL` bắt đầu bằng `https://`.

## Phụ thuộc

Ghim đúng phiên bản trong `package.json` và `package-lock.json`: Nuxt 4.5.2,
Vue 3.5.43, openid-client 6.8.8, image `node:24.21.0-alpine`. Bản chạy (`.output`)
chỉ chứa các gói MIT và BSD; giấy phép từng gói xem `docs/license-decision.md`.

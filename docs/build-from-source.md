<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Build và cài từ mã nguồn không dùng Docker

`make up` dựng mọi thứ bằng Docker. Tài liệu này dành cho người muốn build mã của đội
từ mã nguồn rồi chạy bên ngoài thư mục repo, hoặc gắn vào một hạ tầng đã có sẵn.

| Phần | Tài liệu |
|---|---|
| Ứng dụng DX-Helpdesk (Nuxt, `app/`) | Mục 1 |
| Plugin `dxlab-roles` cho APISIX (`core/gateway/plugins/`) | Mục 2 |
| Data API (`data/`), dịch vụ phân loại (`ai/`) | Chưa cài được bằng `pip install .`, đang làm ở [#141](https://github.com/HaUI-Libre/dx-lab/issues/141) |

Các service còn lại (Keycloak, APISIX, PostgreSQL, Flowable, SeaweedFS) là thành phần
nguồn mở chạy riêng. Ví dụ bên dưới dùng chúng từ `make up`.

## 1. Ứng dụng DX-Helpdesk

### Yêu cầu

- Node.js 24 LTS (`engines` trong `app/package.json`: `>=24.11.0 <25`) và npm đi kèm.
- Keycloak và APISIX đang chạy, ví dụ bằng `make up`. Nếu app trong compose đang chạy,
  dừng nó để nhường cổng: `docker compose stop app`.

### Cấu hình

Không biến nào cần có lúc build. Giá trị trong `app/nuxt.config.ts` là mặc định; biến
`NUXT_*` ghi đè lúc chạy, nên một bản build dùng được cho nhiều môi trường.

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `NUXT_APP_URL` | `http://localhost:3000` | Địa chỉ app mà trình duyệt thấy, dùng tạo `redirect_uri`. Phải khớp redirect URI của client trong realm (`http://localhost:<APP_PORT>/*`) |
| `NUXT_OIDC_ISSUER_INTERNAL` | `http://localhost:8080/realms/dxlab` | Server app đọc discovery và đổi code lấy token ở địa chỉ này |
| `NUXT_OIDC_CLIENT_ID` | `dxlab-app` | Client OIDC |
| `NUXT_OIDC_CLIENT_SECRET` | rỗng, bắt buộc | Client secret, cùng giá trị `KEYCLOAK_CLIENT_SECRET` trong `.env` |
| `NUXT_SESSION_PASSWORD` | rỗng, bắt buộc | Khoá mã hoá cookie phiên, ít nhất 32 ký tự (`openssl rand -hex 32`) |
| `NUXT_GATEWAY_URL` | `http://localhost:9080` | APISIX; mọi lời gọi API đi qua đây |
| `NUXT_PUBLIC_DEMO_LOGIN` | `false` | Hiện nút vào thử bằng tài khoản demo |
| `PORTAL_DATA_DIR` | dò theo thư mục hiện tại | Thư mục chứa `campuses.json` cho trang portal |
| `HOST`, `PORT` | `PORT=3000` | Địa chỉ và cổng server lắng nghe |

Không đọc được `campuses.json` thì server ghi cảnh báo kèm các đường dẫn đã thử, và
portal dùng địa chỉ cơ sở ghi sẵn trong mã.

### Build

```bash
cd app
npm ci          # đúng phiên bản trong package-lock.json
npm run build   # tạo app/.output
```

`.output` là bản chạy hoàn chỉnh: Nitro gom mã server và đúng các gói npm cần lúc chạy,
không cần `node_modules` hay mã nguồn.

### Cài và chạy ngoài repo

```bash
DEST=$HOME/dx-helpdesk
mkdir -p "$DEST/data"
cp -r app/.output "$DEST/"
cp data/samples/campuses.json "$DEST/data/"

cd "$DEST"
NUXT_OIDC_CLIENT_SECRET=<KEYCLOAK_CLIENT_SECRET> \
NUXT_SESSION_PASSWORD=<APP_SESSION_PASSWORD> \
PORTAL_DATA_DIR="$DEST/data" \
node .output/server/index.mjs
```

Kiểm tra:

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:3000/healthz   # 200
```

Mở http://localhost:3000, đăng nhập bằng một tài khoản demo (mục "Tài khoản demo" trong
README), rồi mở `/portal`.

Phiên đăng nhập lưu trong bộ nhớ server: khởi động lại tiến trình thì người dùng đăng
nhập lại. Chạy lâu dài thì đặt tiến trình dưới trình quản lý dịch vụ của hệ điều hành
(ví dụ systemd) với cùng các biến trên.

## 2. Plugin `dxlab-roles` vào APISIX có sẵn

Plugin kiểm tra realm role trong token Keycloak sau khi `openid-connect` đã xác thực,
trả 403 khi thiếu vai trò, rồi chuyển `X-User-Id`, `X-User-Name`, `X-User-Roles` xuống
upstream. Header cùng tên do client gửi bị xoá. Route có `dxlab-roles` mà thiếu
`openid-connect` thì trả 500.

### Yêu cầu

- APISIX 3.x. Đội dùng 3.19.0.
- Plugin `openid-connect` bật trên cùng route.

### Các bước

1. **Chép plugin.** Tên module là `apisix.plugins.dxlab-roles`, nên tệp phải nằm trong
   `apisix/plugins/` dưới thư mục khai báo ở bước 2:

   ```bash
   sudo install -D -m 0644 core/gateway/plugins/apisix/plugins/dxlab-roles.lua \
     /opt/dxlab/apisix/plugins/dxlab-roles.lua
   ```

2. **Khai báo trong `config.yaml`** của APISIX (bản cài từ gói: `/usr/local/apisix/conf/config.yaml`):

   ```yaml
   apisix:
     extra_lua_path: "/opt/dxlab/?.lua"
   plugins:
     # Danh sách này thay hẳn danh sách mặc định: giữ mọi plugin đang dùng, thêm dxlab-roles
     - openid-connect
     - dxlab-roles
   ```

3. **Khởi động lại APISIX**, vì `config.yaml` chỉ được đọc lúc khởi động: `apisix restart`,
   hoặc `sudo systemctl restart apisix` với bản cài từ gói.

4. **Gắn vào route**, cùng `openid-connect`. Ví dụ ở chế độ standalone (`apisix.yaml`):

   ```yaml
   routes:
     - uri: /api/data/*
       plugins:
         openid-connect:
           client_id: dxlab-app
           discovery: http://keycloak:8080/realms/dxlab/.well-known/openid-configuration
           bearer_only: true
           use_jwks: true
           set_userinfo_header: true
         dxlab-roles:
           roles: [ROLE_LAB_MANAGER, ROLE_ADMIN]
       upstream:
         type: roundrobin
         nodes:
           "data-api:8000": 1
   #END
   ```

   Cấu hình đầy đủ của đội ở `core/gateway/apisix.yaml`; giải thích ở
   `core/gateway/README.md`.

5. **Kiểm tra:** không có token thì 401, token thiếu vai trò thì 403, token đủ vai trò
   thì 200.

### Kiểm tra tự động

`make test-lua` chạy `scripts/test-lua-plugin.sh`. Script làm đúng các bước trên với một
APISIX dựng riêng, cần Docker và `openssl`, không cần stack hay `.env`:

1. Tạo container từ image chính thức `apache/apisix:3.19.0-debian`. Đổi phiên bản bằng
   `APISIX_IMAGE`.
2. Chép plugin vào, không mount thư mục repo.
3. Ký token bằng một khoá RSA tạm.
4. Kiểm tra 5 trường hợp:
   - Không có token: 401.
   - Có `X-Userinfo` tự gửi nhưng không có token: 401.
   - Token ký bằng khoá khác: 401.
   - Token đúng nhưng sai vai trò: 403.
   - Token đúng, đúng vai trò: 200.

<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# core/gateway – Apache APISIX

Cửa vào duy nhất cho mọi API của Tầng 2/3, tại http://localhost:9080.

APISIX chạy **standalone**: route nằm trong `apisix.yaml`, không có etcd, không mở
Admin API. Sửa `apisix.yaml` xong APISIX tự nạp lại trong vài giây. Sửa `config.yaml`
hoặc plugin thì cần `docker compose restart apisix`.

| Tệp | Nội dung |
|---|---|
| `config.yaml` | Chế độ standalone, danh sách plugin được bật |
| `apisix.yaml` | Upstream, route, cấu hình xác thực dùng chung |
| `plugins/apisix/plugins/dxlab-roles.lua` | Plugin của đội: kiểm tra realm role, trả 403 |

## Xác thực

Mọi route dùng chung `plugin_configs.auth`:

1. `openid-connect` (`bearer_only`, `use_jwks`): đòi header `Authorization: Bearer <token>`,
   kiểm tra chữ ký bằng JWKS của Keycloak và kiểm tra `iss`. Thiếu token hoặc token
   sai thì trả **401**.
2. `dxlab-roles`: đọc `realm_access.roles` trong token. Không có vai trò nào trong danh
   sách của route thì trả **403**. Qua được thì gửi xuống upstream các header
   `X-User-Id`, `X-User-Name`, `X-User-Roles` (header cùng tên do client gửi bị xoá).
   Service phía sau dùng các header này để biết ai đang gọi, ví dụ ghi `created_by`.

## Route

| Route | Upstream | Vai trò được phép |
|---|---|---|
| `GET /api/me` | trả từ gateway | cả 4 vai trò |
| `/api/data/stats*` | `data-api:8000` | `ROLE_LAB_MANAGER`, `ROLE_ADMIN` |
| `/api/data/*` | `data-api:8000` | cả 4 vai trò |
| `/api/workflow/*` | `flowable:8080/flowable-rest/service/*` | cả 4 vai trò |
| `/api/files/*` | `seaweedfs:8888` | cả 4 vai trò |
| `/api/ai/*` | `ai:8000` | cả 4 vai trò |

Tiền tố `/api/<tên>` được bỏ trước khi chuyển xuống upstream. Data API, Flowable,
SeaweedFS và dịch vụ AI là việc của các issue sau; trước khi có service, request đã
qua xác thực nhận **503**.

`/api/me` trả `sub`, `username`, `name`, `email`, `roles` lấy từ token đã xác thực.
Ứng dụng Nuxt dùng route này để biết người dùng hiện tại và vai trò.

## Kiểm tra

```bash
make up
make smoke
```

`scripts/smoke.sh` lấy token từ Keycloak rồi gọi qua gateway: không token 401,
token `sinhvien` gọi `/api/me` 200, token `sinhvien` gọi `/api/data/stats` 403.

Gọi tay:

```bash
set -a; . ./.env; set +a
TOKEN=$(curl -s -X POST "http://localhost:8080/realms/$KEYCLOAK_REALM/protocol/openid-connect/token" \
  -d grant_type=password -d client_id="$KEYCLOAK_CLIENT_ID" -d client_secret="$KEYCLOAK_CLIENT_SECRET" \
  -d username=sinhvien -d password="$DEMO_USER_PASSWORD" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')
curl -i http://localhost:9080/api/me                                   # 401
curl -i -H "Authorization: Bearer $TOKEN" http://localhost:9080/api/me # 200
curl -i -H "Authorization: Bearer $TOKEN" http://localhost:9080/api/data/stats # 403
```

## Thêm route mới

Thêm một mục vào `routes` trong `apisix.yaml`, luôn kèm `plugin_config_id: auth` và
`dxlab-roles`. `dxlab-roles` trả 500 nếu route không bật `openid-connect`, để tránh
tin nhầm header `X-Userinfo` do client tự gửi. Dòng `#END` cuối tệp là bắt buộc.

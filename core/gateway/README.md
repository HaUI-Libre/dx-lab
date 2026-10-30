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
| `GET /api/workflow/repository/process-definitions` | `flowable:8080/flowable-rest/service/repository/process-definitions` | cả 4 vai trò |
| `/api/workflow/runtime/*`, `/api/workflow/history/historic-*` | Flowable REST | `ROLE_ADMIN`, chỉ để kiểm thử BPMN (#19) |
| `/api/workflow/data/*` | Flowable REST | Data API, cần thêm header `X-Data-Api-Key` khớp `DATA_WORKFLOW_KEY` |
| `/api/files/*` | `seaweedfs:8888/buckets/documents/*` | theo đường dẫn, xem bảng dưới |
| `/api/ai/*` | `ai:8000` | cả 4 vai trò |

Tiền tố `/api/<tên>` được bỏ trước khi chuyển xuống upstream. Flowable REST
vẫn yêu cầu Basic Auth nội bộ: chỉ route workflow thay header Authorization
sau khi Keycloak và `dxlab-roles` đã xác thực Bearer token. Tài khoản REST lấy
từ biến môi trường, không ghi vào route. Thao tác nghiệp vụ trên Flowable chỉ đi qua
Data API, dùng route `/api/workflow/data/*` với khoá nội bộ; route `runtime`/`history`
cho admin chỉ để kiểm thử. Biến môi trường mà Lua trong route đọc bằng `os.getenv`
phải khai trong `nginx_config.envs` của `config.yaml`, nếu không worker nhận `nil`
(lỗi đã gặp ở #98). Xem `core/workflow/README.md`.

Route `/api/files` kiểm tra tên tệp, bỏ query string và thêm header chống chạy
script khi tải về. Xem `core/storage/README.md`.

### Quyền theo đường dẫn trong `/api/files`

| Đường dẫn | `GET`, `HEAD` | `PUT`, `POST`, `DELETE` |
|---|---|---|
| `guides/admin/*` | `ROLE_ADMIN` | `ROLE_LAB_MANAGER`, `ROLE_ADMIN` |
| `guides/technician/*` | `ROLE_TECHNICIAN`, `ROLE_LAB_MANAGER`, `ROLE_ADMIN` | `ROLE_LAB_MANAGER`, `ROLE_ADMIN` |
| `guides/public/*`, phần còn lại của `guides/` | cả 4 vai trò | `ROLE_LAB_MANAGER`, `ROLE_ADMIN` |
| `portal/*` | cả 4 vai trò | `ROLE_LAB_MANAGER`, `ROLE_ADMIN` |
| `tickets/<ticket_id>/*` (ảnh, biên bản phiếu) | người xem được phiếu: admin, trưởng phòng cùng cơ sở, kỹ thuật viên được giao, người tạo | người tạo khi phiếu `DRAFT` hoặc `SUBMITTED` (`409` ở trạng thái khác), admin |
| Đường dẫn khác (`smoke/`) | cả 4 vai trò | `PUT`, `POST`: cả 4 vai trò; `DELETE`: không mở |

Mỗi dòng có route riêng với `priority` cao hơn route chung `/api/files/*`, nên được
chọn trước. Mọi route `/api/files` dùng chung `plugin_config` `files`.

Route `files-tickets` cần thêm plugin `forward-auth` (bật trong `config.yaml`): trước
khi chuyển tới SeaweedFS, gateway gửi token người gọi cùng `X-Forwarded-Uri`,
`X-Forwarded-Method` tới `GET /auth/ticket-files` của Data API. Data API áp cùng quy tắc
xem phiếu như `GET /tickets/{id}` và trả `403`, `404` hoặc `409` để gateway chặn
(#185, #186). Filer chạy với `-filer.disableDirListing` nên không liệt kê được thư mục.

Quyền nằm ở gateway. Trường `allowedRoles` trong metadata tài liệu của portal
(`portal/manifest.json`, `*.meta.json`) chỉ để app chọn tài liệu hiển thị, không dùng
để cấp quyền.

Request có `..` hoặc `%2e` (không phân biệt hoa thường) trong dòng request gốc bị trả
**403**. nginx gộp `/../` và giải mã `%2e` trước khi chọn route, nên nếu không chặn thì
`guides/public/../admin/x` đi theo route của `guides/admin/`. Plugin `uri-blocker` của
APISIX 3.19 so trên URI đã chuẩn hoá nên không bắt được hai dạng này; phần chặn nằm
trong `serverless-post-function` của `plugin_config` `files`.

Data API và dịch vụ AI là việc của các issue sau; trước khi có service, request
đã qua xác thực nhận **503**.

`/api/me` trả `sub`, `username`, `name`, `email`, `roles` và `co_so` (khi token có
claim này, #74) lấy từ token đã xác thực. Ứng dụng Nuxt dùng route này để biết người
dùng hiện tại, vai trò và cơ sở. Phản hồi do gateway tự sinh (`/api/me`, lỗi 400/403)
đều có `Content-Type: application/json`.

CORS chỉ cho origin của ứng dụng Nuxt, lấy từ `APP_URL` (`http://localhost:${APP_PORT}`).

## Kiểm tra

```bash
make up
make smoke
```

`scripts/smoke.sh` lấy token từ Keycloak rồi gọi qua gateway: không token 401,
token `sinhvien` gọi `/api/me` 200, token `sinhvien` gọi `/api/data/stats` 403,
lấy được danh sách process definition, tải lên rồi tải về một tệp. Sau đó gọi
thẳng gateway, không qua app, để kiểm tra quyền theo đường dẫn trong `/api/files` và
việc chặn `..`, `%2e`.

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

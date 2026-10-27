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

Sau khi sửa mã trong `app/` hoặc `git pull`, chạy lại `make up`: lệnh này dựng lại image
từ mã hiện tại.

Phát triển có hot reload trên máy host (cần Node.js 24 LTS), trong khi các service
khác vẫn chạy bằng `make up`:

```bash
docker compose stop app
cd app && npm ci
NUXT_OIDC_CLIENT_SECRET=<KEYCLOAK_CLIENT_SECRET> \
NUXT_SESSION_PASSWORD=<APP_SESSION_PASSWORD> npm run dev
```

Build bản chạy (`npm run build`), chép `.output` ra ngoài repo và chạy bằng Node, không
dùng Docker: [docs/build-from-source.md](../docs/build-from-source.md).

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

## Báo hỏng và quy trình sửa chữa [P] (#26)

| Trang | Ai dùng | Nội dung |
|---|---|---|
| `/tickets` | Mọi vai trò | Sinh viên: yêu cầu của mình. Kỹ thuật viên: việc được giao tại cơ sở mình. Trưởng phòng: hàng đợi cơ sở mình. Lọc theo trạng thái, tìm theo chữ |
| `/tickets/new` | Mọi vai trò | Chọn "Thiết bị của tôi" hoặc nhập mã tài sản; chọn vị trí; tiêu đề, mô tả, loại, ưu tiên; tối đa 3 ảnh |
| `/tickets/{id}` | Theo quyền xem của Data API | Chi tiết, ảnh, lịch sử; nút theo vai trò và trạng thái |

Nút trên trang chi tiết:

| Trạng thái | Người thấy nút | Nút |
|---|---|---|
| `DRAFT` | Người tạo | Gửi yêu cầu, Xoá bản nháp |
| `SUBMITTED`, chưa tiếp nhận | Trưởng phòng cùng cơ sở, admin | Tiếp nhận; Từ chối (bắt buộc lý do) |
| `SUBMITTED`, đã tiếp nhận | Trưởng phòng cùng cơ sở, admin | Phân công: chỉ liệt kê kỹ thuật viên cùng cơ sở (`GET /api/data/technicians`), chỉnh ưu tiên |
| `ASSIGNED` | Kỹ thuật viên được giao | Nhận việc |
| `IN_PROGRESS` | Kỹ thuật viên được giao | Đánh dấu hoàn thành (bắt buộc biên bản) |
| `RESOLVED` | Trưởng phòng cùng cơ sở, admin | Nghiệm thu và đóng; Mở lại (bắt buộc lý do) |
| `CLOSED` | Người tạo, khi chưa đánh giá | Đánh giá 1–5 |

Nút chỉ là gợi ý giao diện; Data API kiểm tra lại vai trò, cơ sở, người được giao và
trạng thái ở mỗi bước.

Ảnh tải lên `/gw/api/files/tickets/<ticket_id>/<uuid>.<đuôi>` rồi đăng ký qua
`POST /api/data/tickets/{id}/attachments`. Lưu nháp hoặc gửi đều tạo ticket trước để
có `ticket_id` cho đường dẫn ảnh.

**Thiết bị của tôi** gọi `GET /api/assets/me`, tra mã dán trên máy gọi
`GET /api/assets/bytag/{tag}` (dịch vụ tích hợp tài sản, #72). Giao diện chờ mỗi thiết
bị có `id` (ID tài sản trên Snipe-IT, thành `asset_id` của ticket), `asset_tag`, và nếu
có thì `name`, `location_id` (khớp `site_locations`), `location`. Khi hai route này lỗi,
kể cả khi profile `integration` tắt, trang báo chưa kết nối được hệ thống tài sản; người
báo chọn vị trí bằng tay, mã tài sản đã nhập được ghi vào mô tả, ticket gửi không cần
`asset_id`.

**Thống kê (#27).** `/dashboard`, chỉ hiện trong menu với trưởng phòng và admin, gọi
`GET /api/data/stats`; admin thêm `?co_so=CS1|CS2|CS3` hoặc để trống để xem cả ba cơ sở.
Trang chờ hình dạng `TicketStats` trong `data/openapi.yaml` (`total`, `by_status`,
`by_category`, `by_co_so`, `average_resolution_hours`, `overdue_count`,
`reopen_count`; #22). Phân quyền theo cơ sở do Data API làm; vai
trò khác thấy thông báo, API trả 403. Khi `/stats` chưa có, trang ghi "Chưa có API
thống kê". Trang nạp lại số liệu khi nhận sự kiện đổi trạng thái phiếu qua SSE (gộp
sự kiện trong 1 giây; admin đang chọn một cơ sở thì bỏ qua sự kiện của cơ sở khác). Biểu
đồ thanh vẽ bằng CSS, không thêm thư viện.

**Gợi ý phân loại (#32, kịch bản 6).** Khi mô tả có từ 15 ký tự, form gọi
`POST /api/ai/classify` qua gateway với `{"title", "description"}` (chờ 0,7 giây sau lần
gõ cuối). Giao diện chờ phản hồi có `category` (mã trong `CATEGORY_LABELS`), `priority`
(mã trong `PRIORITY_LABELS`), và nếu có thì `keywords` (danh sách từ khoá dẫn tới kết
quả) và `source` (`model` hoặc `rules`, cho biết gợi ý đến từ mô hình hay luật dự
phòng). Gợi ý chỉ hiện ra; loại và mức ưu tiên chỉ đổi khi người dùng bấm "Dùng gợi
ý", và người dùng vẫn sửa được trước khi gửi. Trưởng phòng chốt mức ưu tiên cuối cùng
ở bước phân công. Dịch vụ phân loại lỗi hoặc chưa chạy thì form ghi "Chưa có gợi ý" và
vẫn gửi bình thường; gợi ý không gọi bước nào của quy trình.

`make smoke` gọi `scripts/test-app-tickets.sh`: đăng nhập bằng phiên thật của ba vai
trò, đi một vòng có mở lại và kiểm tra trang render đúng nút cho từng người.

## Cổng thông tin [H] (Portal tối giản - #25)

Không gian Con người số [H] tại `/portal`:
- **Hồ sơ cá nhân**: Tên, tài khoản, email, vai trò nghiệp vụ (4 vai trò: `ROLE_STUDENT`, `ROLE_TECHNICIAN`, `ROLE_LAB_MANAGER`, `ROLE_ADMIN`) và thuộc tính cơ sở làm việc (`co_so`: CS1, CS2, CS3), định danh OIDC `sub`.
- **Nhóm & Đơn vị**: Tổ kỹ thuật và quản lý phòng lab tại 3 cơ sở đào tạo HaUI (CS1 - Bắc Từ Liêm, CS2 - Tây Tựu, CS3 - Hà Nam), hotline (mô tả liên hệ phòng ban), email hỗ trợ và phân định trách nhiệm luồng nghiệp vụ.
- **Tài liệu hướng dẫn**:
  - Tải lên (`PUT /gw/api/files/...`), xem trực tiếp (preview) và tải về qua `/api/files` của APISIX kết nối SeaweedFS (bucket `documents`).
  - Phân quyền tài liệu theo thư mục lưu trữ trên SeaweedFS qua API Gateway: `portal/` và `guides/public/` (mọi vai trò đọc), `guides/technician/` (kỹ thuật viên trở lên đọc), `guides/admin/` (chỉ admin đọc). Quyền ghi chỉ dành cho Trưởng phòng lab (`ROLE_LAB_MANAGER`) và Quản trị viên (`ROLE_ADMIN`); giao diện ẩn nút tải lên với sinh viên và kỹ thuật viên. Trường `allowedRoles` trong metadata chỉ dùng để hiển thị nhãn và lọc sơ bộ trên giao diện.
  - API phục vụ giao diện: `GET /api/portal/documents`, `POST /api/portal/documents`, `GET /api/portal/groups`.

## Cấu hình

| Biến (`.env`) | Biến trong container | Ý nghĩa |
|---|---|---|
| `APP_PORT` | `NUXT_APP_URL` | Cổng của app; dùng chung cho redirect URI trong realm và CORS ở gateway |
| `APP_SESSION_PASSWORD` | `NUXT_SESSION_PASSWORD` | Khoá mã hoá cookie phiên, ít nhất 32 ký tự (`openssl rand -hex 32`) |
| `KEYCLOAK_CLIENT_ID`, `KEYCLOAK_CLIENT_SECRET` | `NUXT_OIDC_CLIENT_ID`, `NUXT_OIDC_CLIENT_SECRET` | Client OIDC |
| `KEYCLOAK_REALM` | `NUXT_OIDC_ISSUER_INTERNAL` | Địa chỉ Keycloak trong mạng compose |
| | `NUXT_GATEWAY_URL` | `http://apisix:9080` |
| | `PORTAL_DATA_DIR` | Thư mục chứa `campuses.json`; image đặt `/app/data/samples` |

Đổi `APP_PORT` sau khi đã chạy lần đầu thì realm cũ vẫn giữ redirect URI cũ (realm
chỉ import một lần): xem mục "Sửa realm" trong `core/identity/README.md`.

## Giới hạn đã biết

- Phiên lưu trong bộ nhớ: khởi động lại container `app` thì người dùng đăng nhập lại.
- HTTP thuần, đúng với Keycloak `start-dev`; chạy HTTPS thì cookie tự bật `Secure`
  khi `NUXT_APP_URL` bắt đầu bằng `https://`.
- Lưu trữ metadata tài liệu qua tệp sidecar `<filePath>.meta.json` và `portal/manifest.json` trên SeaweedFS sử dụng khóa `AsyncMutex` trong Nitro server để tránh ghi đè đồng thời. Về dài hạn, metadata tài liệu sẽ được chuyển giao về Data API (#20) quản lý trên PostgreSQL để hỗ trợ giao dịch CSDL ACID và tìm kiếm toàn văn.

## Phụ thuộc

Ghim đúng phiên bản trong `package.json` và `package-lock.json`: Nuxt 4.5.2,
Vue 3.5.43, openid-client 6.8.8, image `node:24.21.0-alpine`. Bản chạy (`.output`)
chỉ chứa các gói MIT và BSD; giấy phép từng gói xem `docs/license-decision.md`.

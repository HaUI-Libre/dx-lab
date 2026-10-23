<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Dịch vụ tích hợp tài sản (#72)

`asset-sync` nằm ở Tầng 2, profile `integration`. Chỉ adapter trong thư mục này
gọi Snipe-IT `/api/v1`; không truy cập MariaDB. Token Snipe-IT được đọc từ volume
`snipeit-token` ở chế độ chỉ đọc. Giao diện và Data API gọi dịch vụ qua APISIX
`/api/assets/*` với Keycloak Bearer token. Dịch vụ kiểm tra lại chữ ký và vai trò.

| Route | Kết quả |
|---|---|
| `GET /api/assets/me` | Thiết bị của `preferred_username` trong token; tra đúng username trên Snipe-IT |
| `GET /api/assets/bytag/{tag}` | Thiết bị theo mã dán |
| `GET /api/assets/by-id/{id}` | Vị trí hiện tại của thiết bị để Data API định tuyến ticket |
| `GET /api/assets/locations/{id}/assets` | Thiết bị trong phòng/vị trí |
| `POST /api/assets/internal/status` | Data API cập nhật `IN_PROGRESS`/`CLOSED`; cần thêm `X-Data-Api-Key` |
| `GET /api/assets/internal/failures` | Danh sách lần cập nhật thất bại hoặc đang chờ; cần khóa nội bộ |
| `POST /api/assets/internal/retry/{ticket_id}` | Thử lại ngay; cần khóa nội bộ |

Các route đọc trả `id`, `asset_tag`, `name`, `location_id`, `location`, `co_so`.
`co_so` được suy từ cây vị trí tới ID cơ sở gốc theo `ASSET_SITE_ROOTS` (mẫu:
`1:CS1,9:CS2,15:CS3`); không lấy từ request của trình duyệt. Khi không tìm được
vị trí, `co_so` là `null`.

Data API gọi `POST /internal/status` sau khi ticket vào `IN_PROGRESS` hoặc `CLOSED`.
Payload gồm `ticket_id`, `asset_id`, `to_status` và `resolution_summary` khi đóng.
SQLite trong volume `asset-sync-data` lưu nhãn ban đầu theo ticket **trước** khi
PATCH Snipe-IT. Khi đóng, dịch vụ trả nhãn này về và thêm số ticket, biên bản vào
ghi chú tài sản. Lỗi Snipe-IT trả 503 cho Data API ghi audit; bản ghi lỗi được
thử lại tự động sau `ASSET_RETRY_SECONDS` (mặc định 60 giây) và có thể thử thủ công qua API nội bộ. Trạng thái
ticket/Flowable không bị rollback khi Snipe-IT lỗi.

Chạy `make demo` để bật profile. `make up` không khởi động Snipe-IT hoặc asset-sync;
form báo hỏng vẫn cho chọn vị trí thủ công. `DATA_ASSET_KEY` được `make env` sinh
ngẫu nhiên; không dùng `changeme`. Thay nhãn và cây vị trí bằng
`ASSET_REPAIR_LABEL`, `ASSET_SITE_ROOTS` trong `.env` khi tích hợp khách hàng khác.

Chạy test adapter với Snipe-IT giả lập: `make test` hoặc
`python3 -m pytest -q tests/test_asset_sync.py`. Cần kiểm thử thực tế qua gateway
với profile `integration` để xác nhận quyền API và nhãn tài sản trên Snipe-IT.

<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# data/

Data API (FastAPI): ticket, workflow, schema và dữ liệu mẫu.

## Chạy dịch vụ (#20)

`make up` dựng `data-api` cùng core; startup áp dụng `schema.sql` cho database trống
hoặc các migration chưa áp dụng cho database đã có schema. Mọi request đi qua APISIX
`/api/data/*`, Swagger tại `/api/data/docs`. Cần đổi `DATA_WORKFLOW_KEY` trong
`.env` thành chuỗi ngẫu nhiên trước khi chạy; Data API dùng khóa này cùng Bearer
token Keycloak để gọi tuyến workflow nội bộ qua APISIX. Data API kiểm tra chữ ký,
issuer, client và role của token một lần nữa.

`POST /tickets` tạo `DRAFT`; `PATCH`/`DELETE /tickets/{id}` chỉ cho người tạo
bản nháp. `GET /tickets` hỗ trợ status/category/priority/q/page/page_size.
`POST /tickets/{id}/actions/{action}` nhận `submit`, `accept`, `reject`, `assign`,
`start`, `resolve`, `close`, `reopen` và hoàn tất task Flowable tương ứng. API không
cho đặt `status`/`co_so` trực tiếp. `submit` cần category, priority, `asset_id`
và `location_id`; Data API tra `site_locations` để điền `co_so`.

Phân công nhận Keycloak `technician_sub`, kiểm tra vai trò kỹ thuật viên và
thuộc tính `co_so` qua Keycloak Admin API, rồi dùng username của kỹ thuật viên
cho assignee Flowable. Trạng thái và task được kiểm tra trước khi hoàn tất.
Các lời gọi Flowable thực hiện khi khóa transaction ticket còn giữ; nếu Flowable
từ chối, transaction PostgreSQL rollback. Lỗi commit PostgreSQL sau khi Flowable
đã nhận lệnh vẫn cần đối soát thủ công giữa hai hệ thống.

M2 chưa có dịch vụ tích hợp tài sản chạy trong Compose, nên `location_id` của
thiết bị hiện do client chuyển từ danh mục thiết bị; Data API chỉ tin bảng ánh
xạ cơ sở nội bộ, không nhận `co_so` do client đặt. Khi dịch vụ tài sản được
triển khai, cần xác minh `asset_id` và vị trí thiết bị qua API tài sản ở bước
`submit`. Dữ liệu mẫu trước đây chỉ có asset tag, không có Snipe-IT ID; migration
lưu tag cũ vào `ticket_legacy_asset_refs`, `asset_id` còn trống để đối soát.

## Metadata và provenance (#21)

`GET /api/data/tickets/{id}/events` trả lịch sử theo `occurred_at, id` cho người
có quyền xem ticket. `GET /api/data/tickets/{id}/provenance` trả `source`, người tạo,
thời điểm tạo/cập nhật/xóa, toàn bộ sự kiện và `reopen_count`; chủ ticket và admin
vẫn có thể xem lịch sử bản nháp đã xóa mềm. Sự kiện `EDIT`, `ASSIGN`, `RATE`
giữ giá trị trước/sau; `REJECT` và `REOPEN` giữ lý do; `ticket_events` chỉ cho phép
thêm, không cho sửa/xóa. Nguồn hợp lệ là `dx-helpdesk`, `snipe-it`, `nats`.

Khi ticket chuyển sang `IN_PROGRESS` hoặc `CLOSED`, Data API ghi sự kiện
`ASSET_STATUS_UPDATE_PENDING` cùng transaction rồi thử gọi URL cấu hình
`DATA_ASSET_STATUS_URL` với token người thao tác. Kết quả được ghi bằng
`ASSET_STATUS_UPDATE_SUCCEEDED` (nguồn `snipe-it`) hoặc
`ASSET_STATUS_UPDATE_FAILED` (nguồn `dx-helpdesk`, kèm mã lỗi/HTTP status).
Lỗi tích hợp không đổi trạng thái ticket. URL phải trỏ qua APISIX tới tuyến
`/api/assets/*` nội bộ của dịch vụ tích hợp #72, yêu cầu thêm header
`X-Data-Api-Key` từ `DATA_ASSET_KEY`, nhận
JSON `ticket_id`, `asset_id`, `to_status` và
`resolution_summary` khi đóng; chỉ trả 2xx sau khi Snipe-IT đã cập nhật. Khi URL
chưa cấu hình, sự kiện thất bại ghi `integration_not_configured`; sự kiện pending
giúp tìm lần cần thử lại. #72 sẽ cung cấp route và cơ chế thử lại thực tế.

## Hợp đồng ban đầu (issue #16)

- `schema.sql` là schema đầu tiên cho database `dxdata` trên PostgreSQL. `migrations/001_data_api.sql` nâng cấp schema cũ mà giữ asset tag; `002_provenance.sql` giới hạn nguồn và bảo vệ sự kiện append-only.
- `openapi.yaml` mô tả CRUD, hành động workflow, đọc provenance và đánh giá; attachment metadata và thống kê là phạm vi các issue sau.
- `tickets` lưu ticket, trạng thái, người tạo, người được giao và ID process instance của Flowable. `ticket_attachments` chỉ lưu metadata và khóa đối tượng SeaweedFS. `ticket_events` lưu lịch sử thay đổi dữ liệu; lịch sử task/process vẫn do Flowable quản lý.
- `created_by`, `assigned_to` và `actor_sub` là Keycloak subject, không phải foreign key tới database của Keycloak. API phải suy ra người dùng từ token và kiểm tra quyền trên server.
- API công khai chỉ cho sửa/xóa bản nháp. Việc gửi, phân công, xử lý, nghiệm thu hoặc từ chối ticket phải đi theo luồng Flowable; tích hợp đồng bộ trạng thái với Data API sẽ được chốt khi triển khai workflow. Không cập nhật `status` trực tiếp từ trình duyệt.
- Xóa bản nháp là xóa mềm (`deleted_at`) để giữ lịch sử. Ảnh/tệp được tải qua `/api/files` trước khi đăng ký metadata, và API phải xác minh khóa đối tượng thuộc người dùng/ticket.

## Dữ liệu mẫu 3 cơ sở HaUI (issue #23)

- Thư mục `samples/` chứa dữ liệu mẫu cho Đại học Công nghiệp Hà Nội (HaUI):
  - `campuses.json`: Danh mục 3 cơ sở (`CS1`, `CS2`, `CS3`), địa chỉ, tòa nhà, phòng máy. Tọa độ và ranh giới là ước lượng, do đội tự xác định để minh họa.
  - `snipeit_seed.json`: Cây vị trí, nhãn trạng thái ("Sẵn sàng", "Đang sửa chữa"), danh mục, model, người dùng trùng Keycloak và danh sách tài sản để nạp vào Snipe-IT.
  - `tickets_seed.sql`: Script nạp vào PostgreSQL `dxdata` chứa các trạng thái (`DRAFT`, `SUBMITTED`, `ASSIGNED`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`, `REJECTED`, nhánh `REOPEN`) kèm bảng sự kiện `ticket_events` và đính kèm `ticket_attachments`.
  - `tickets.json`: Snapshot JSON của các ticket mẫu phục vụ kiểm thử độc lập và demo offline.
  - `training_data.jsonl`: 160 mẫu báo hỏng tiếng Việt có nhãn `category` và `priority` phục vụ huấn luyện mô hình phân loại scikit-learn (M3.22).
- Chạy `make seed` để nạp dữ liệu mẫu vào SeaweedFS và PostgreSQL `dxdata` (hoặc `python3 scripts/seed.py --dry-run` để kiểm tra tính toàn vẹn). Chi tiết xem [data/samples/README.md](samples/README.md).


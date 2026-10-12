<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# data/

Data API (FastAPI): schema, provenance, dữ liệu mẫu.

## Hợp đồng ban đầu (issue #16)

- `schema.sql` là schema đầu tiên cho database `dxdata` trên PostgreSQL. Chạy một lần trên database trống; các thay đổi tiếp theo cần migration. File này chỉ định nghĩa dữ liệu, chưa dựng dịch vụ FastAPI.
- `openapi.yaml` là hợp đồng dự kiến tại `/api/data` qua APISIX. Các endpoint trong file chưa được triển khai; issue #20 sẽ làm CRUD, #21 làm provenance và #22 làm thống kê.
- `tickets` lưu ticket, trạng thái, người tạo, người được giao và ID process instance của Flowable. `ticket_attachments` chỉ lưu metadata và khóa đối tượng SeaweedFS. `ticket_events` lưu lịch sử thay đổi dữ liệu; lịch sử task/process vẫn do Flowable quản lý.
- `created_by`, `assigned_to` và `actor_sub` là Keycloak subject, không phải foreign key tới database của Keycloak. API phải suy ra người dùng từ token và kiểm tra quyền trên server.
- API công khai chỉ cho sửa/xóa bản nháp. Việc gửi, phân công, xử lý, nghiệm thu hoặc từ chối ticket phải đi theo luồng Flowable; tích hợp đồng bộ trạng thái với Data API sẽ được chốt khi triển khai workflow. Không cập nhật `status` trực tiếp từ trình duyệt.
- Xóa bản nháp là xóa mềm (`deleted_at`) để giữ lịch sử. Ảnh/tệp được tải qua `/api/files` trước khi đăng ký metadata, và API phải xác minh khóa đối tượng thuộc người dùng/ticket.

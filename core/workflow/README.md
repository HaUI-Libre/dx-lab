<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Flowable REST (issue #15)

`docker-compose.yml` chạy `flowable/flowable-rest:7.2.0` headless trên database
`flowable` do `core/postgres/init/01-create-databases.sh` tạo ở lần khởi tạo
PostgreSQL đầu tiên. Flowable tự tạo bảng engine trong database này. Service
không mở cổng ra máy host; APISIX chuyển
`GET /api/workflow/repository/process-definitions` tới
`/flowable-rest/service/repository/process-definitions` trên mạng Compose.

## Chạy và kiểm tra

1. Sao chép `.env.example` thành `.env`, thay mọi giá trị `changeme`, nhất là
   `FLOWABLE_DB_PASSWORD` và `FLOWABLE_ADMIN_PASSWORD`.
2. Chạy `make up`, rồi xem `docker compose logs flowable` cho tới khi REST app
   khởi động xong. Chạy `make smoke` để kiểm tra request không token nhận 401
   và request có token Keycloak gọi được API liệt kê process definition qua gateway.
3. Có thể xem JSON trực tiếp bằng token của một tài khoản demo:

   ```bash
   curl -H "Authorization: Bearer <access-token>" \
     http://localhost:9080/api/workflow/repository/process-definitions
   ```

Danh sách `data` có thể rỗng: BPMN của DX-Helpdesk thuộc issue #18 và việc
deploy tự động thuộc issue #19. Không bật process demo mặc định của Flowable.

## Xác thực và giới hạn hiện tại

APISIX xác thực token Keycloak và vai trò trước, sau đó dùng tài khoản REST
nội bộ từ `.env` để gọi Flowable. Basic credential không nằm trong
`apisix.yaml` và không được gửi cho trình duyệt. Flowable vẫn nhìn thấy một
tài khoản REST chung; issue tích hợp quy trình sau này cần truyền danh tính
người thực hiện vào process/task audit một cách tường minh.
Gateway chỉ công bố API liệt kê process definition trong issue này; cần thêm
route và quyền tương ứng khi triển khai thao tác workflow ở các issue sau.

Nếu PostgreSQL volume đã tồn tại trước khi database `flowable` được thêm vào
script khởi tạo, script sẽ không tự chạy lại. Kiểm tra/tạo database và user
trong volume hiện có; tránh `docker compose down -v` vì lệnh đó xóa dữ liệu.

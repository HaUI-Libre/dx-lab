<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Khung slide 12 trang (#41, bản nháp)

Mỗi slide một ý; chữ trên slide ngắn, phần nói nằm trong kịch bản demo. Hình lấy từ
`docs/images/` và ảnh chụp màn hình app, Snipe-IT, Grafana.

| # | Tiêu đề | Nội dung chính | Hình |
|---|---|---|---|
| 1 | DX-Lab: Trạm điều hành số trên DX-OS Open-Core | Tên đội, thành viên, trường, link repo | Logo, mã QR tới repo |
| 2 | Bài toán | 3 cơ sở, phần mềm tài sản có sẵn; báo hỏng rời rạc; cần nền tảng dùng chung, không thay hệ thống cũ | Sơ đồ hiện trạng |
| 3 | Kiến trúc 3 tầng | Open-Core headless, H-P-D-I, DX-Helpdesk; mọi lời gọi qua APISIX | `architecture-3-tier.svg` |
| 4 | 7 lớp công nghệ của đề | Bảng ánh xạ lớp vào thành phần và tầng | Bảng từ `architecture.md` mục 2 |
| 5 | Tích hợp hệ thống tài sản | Snipe-IT ngoài DX-OS, `asset-sync` gọi REST, sự kiện NATS, không đọc DB | `integration-architecture.svg` |
| 6 | Quy trình BPMN | Tiếp nhận, từ chối có lý do, phân công cùng cơ sở, xử lý, nghiệm thu, mở lại | `helpdesk-workflow.svg` |
| 7 | Demo trực tiếp | Chuyển sang app | |
| 8 | Định tuyến và phân quyền theo cơ sở | Thuộc tính `co_so`, không thêm vai trò; lọc ở Data API | Ảnh hàng đợi CS1 và CS2 |
| 9 | Giám sát | Prometheus, Grafana; số liệu gateway, quy trình, tài sản | Ảnh dashboard Grafana |
| 10 | Tính mở và chuẩn mở | OIDC, BPMN 2.0, OpenAPI 3, GeoJSON, Prometheus; dữ liệu và cấu hình đều nằm trong repo | Bảng chuẩn mở |
| 11 | Giấy phép và kiểm soát chất lượng | Apache-2.0, NOTICE, REUSE 121/121, gitleaks, DCO, 5 check bắt buộc, CI dựng stack từ máy sạch | Ảnh trang Actions |
| 12 | Kết quả và hướng tiếp | Đã chạy, còn lại (thống kê #22, phân loại #31, định tuyến vùng #79); cảm ơn | |

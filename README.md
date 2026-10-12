<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# DX-Lab HaUI – Trạm điều hành số trên nền tảng DX-OS Open-Core

[![CI](https://github.com/HaUI-Libre/dx-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/HaUI-Libre/dx-lab/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

Bài dự thi **Phần mềm nguồn mở – PMNM HaUI 2026** (vòng tuyển chọn cấp trường),
bám chủ đề OLP PMNM 2026 của VFOSSA: *Xây dựng Hệ điều hành Chuyển đổi số bằng
Công nghệ Lõi nguồn mở (DX-OS Open-Core)*.

> Dự án đang phát triển theo milestone. Mục ghi *(sắp có)* chưa được triển khai.

## Kiến trúc 3 tầng

```
┌──────────────────────────────────────────────────────────────────┐
│ Tầng 3 – Ứng dụng nghiệp vụ                                       │
│   DX-Helpdesk: tiếp nhận & xử lý yêu cầu hỗ trợ CNTT / thiết bị   │
├──────────────────────────────────────────────────────────────────┤
│ Tầng 2 – Không gian năng lực H-P-D-I (có giao diện người dùng)    │
│   [H] Portal, người dùng/nhóm, tài liệu                           │
│   [P] Quy trình có trạng thái, hàng đợi xử lý, lịch sử            │
│   [D] Dữ liệu thống nhất, provenance, dashboard, REST API         │
│   [I] Phân loại/ưu tiên yêu cầu, hỏi–đáp tài liệu (RAG)           │
├──────────────────────────────────────────────────────────────────┤
│ Tầng 1 – DX-OS Open-Core (headless, KHÔNG có UI người dùng cuối)  │
│   Identity/SSO (Keycloak) · API Gateway (Apache APISIX)           │
│   Dữ liệu cấu trúc (PostgreSQL) · Phi cấu trúc (SeaweedFS)        │
│   Workflow (Flowable)                                             │
└──────────────────────────────────────────────────────────────────┘
```

Nguyên tắc: **mọi lời gọi từ Tầng 2/3 đều đi qua API Gateway**, được xác thực
bằng token do Keycloak cấp. Đổi ứng dụng nghiệp vụ không cần sửa Open-Core.

Chi tiết: [docs/architecture.md](docs/architecture.md)

## Cấu trúc thư mục

| Thư mục | Nội dung | Phụ trách |
|---|---|---|
| `core/` | Cấu hình Open-Core: identity, gateway, workflow, storage | Trung |
| `data/` | Data API (FastAPI), schema, dữ liệu mẫu | Nam Anh |
| `ai/` | Dịch vụ Intelligence: phân loại, RAG | Nam Anh |
| `app/` | Giao diện H-P-D-I và ứng dụng DX-Helpdesk (Nuxt 3) | Trung |
| `docs/` | Kiến trúc, quy trình BPMN, bảng license, báo cáo | Linh |
| `scripts/` | Script tiện ích (kiểm tra SPDX, seed dữ liệu…) | Cả đội |

## Cài đặt và chạy

Yêu cầu: Docker 24+ với Docker Compose v2.17+, Git, `make`, `curl`; khuyến nghị 16 GB RAM.

```bash
git clone https://github.com/HaUI-Libre/dx-lab.git
cd dx-lab
cp .env.example .env      # đổi các giá trị changeme; KHÔNG commit file này
make up                   # dựng các service Tầng 1, chờ tới khi healthy
make smoke                # kiểm tra gateway: 401 / 200 / 403, workflow, tải tệp
```

Lần đầu chạy mất vài phút để tải image. `make help` liệt kê các lệnh khác.
`docker compose down -v` xoá toàn bộ dữ liệu (database, tệp, realm).

| Service | Địa chỉ trên máy | Ghi chú |
|---|---|---|
| API Gateway (APISIX) | http://localhost:9080 | Cửa vào duy nhất cho Tầng 2/3 |
| Keycloak | http://localhost:8080 | Đăng nhập, admin console tại `/admin` |
| PostgreSQL | `localhost:5432` | Chỉ để phát triển; `make psql` |
| Flowable, SeaweedFS | không mở ra ngoài | Chỉ gọi qua gateway |

Mọi cổng chỉ mở trên `127.0.0.1`.

## Tài khoản demo

Tạo tự động khi Keycloak khởi tạo lần đầu, mật khẩu chung là `DEMO_USER_PASSWORD` trong `.env`.

| Username | Vai trò |
|---|---|
| `sinhvien` | `ROLE_STUDENT` |
| `kythuatvien` | `ROLE_TECHNICIAN` |
| `truongphong` | `ROLE_LAB_MANAGER` |
| `quantri` | `ROLE_ADMIN` |

Lấy token và gọi API: xem [core/identity/README.md](core/identity/README.md).

## API qua gateway

| Route | Trạng thái |
|---|---|
| `GET /api/me` | Đã chạy: thông tin người dùng và vai trò từ token |
| `/api/files/*` | Đã chạy: tải lên, tải về tệp ([core/storage](core/storage/README.md)) |
| `GET /api/workflow/repository/process-definitions` | Đã chạy ([core/workflow](core/workflow/README.md)) |
| `/api/data/*` | *(sắp có)*; hợp đồng tại [data/openapi.yaml](data/openapi.yaml) |
| `/api/ai/*` | *(sắp có)* |

Chi tiết xác thực và phân quyền: [core/gateway/README.md](core/gateway/README.md).

## Thành phần nguồn mở và giấy phép

Xem [docs/dependencies.md](docs/dependencies.md).

## Đóng góp

Đọc [CONTRIBUTING.md](CONTRIBUTING.md). Báo lỗi và đề xuất tính năng qua
[Issues](https://github.com/HaUI-Libre/dx-lab/issues).

## Giấy phép

Phát hành theo [Apache License 2.0](LICENSE).

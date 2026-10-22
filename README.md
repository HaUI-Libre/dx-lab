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
│   [I] Phân loại, gợi ý mức ưu tiên yêu cầu (scikit-learn)         │
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
| `ai/` | Dịch vụ Intelligence: phân loại, gợi ý mức ưu tiên | Nam Anh |
| `app/` | Giao diện H-P-D-I và ứng dụng DX-Helpdesk (Nuxt 4) | Trung |
| `docs/` | Kiến trúc, quy trình BPMN, bảng license, báo cáo | Linh |
| `scripts/` | Script tiện ích (smoke test, seed dữ liệu…) | Cả đội |

## Cài đặt và chạy

Yêu cầu, toàn bộ là phần mềm nguồn mở:

- [Docker Engine](https://docs.docker.com/engine/install/) 24+ (Apache-2.0) và
  [Docker Compose plugin](https://docs.docker.com/compose/install/linux/) v2.17+ (Apache-2.0)
- Git, `make`, `curl`, `bash`, Python 3 (thư viện chuẩn)
- Khuyến nghị 16 GB RAM

Không cần Docker Desktop. Docker Desktop không phải phần mềm nguồn mở
(xem [docs/license-decision.md](docs/license-decision.md)).

**Windows:** chạy trong WSL2.

1. Trong PowerShell (quyền admin): `wsl --install -d Ubuntu`, khởi động lại máy.
2. Mở Ubuntu, cài Docker Engine và Compose plugin theo
   [hướng dẫn cho Ubuntu](https://docs.docker.com/engine/install/ubuntu/), rồi
   `sudo apt install make curl git`.
3. Clone repo **trong hệ thống tệp của WSL** (ví dụ `~/dx-lab`), không clone vào `C:\`,
   để tránh lỗi xuống dòng CRLF và để bind mount chạy nhanh.
4. Chạy các lệnh dưới đây trong terminal Ubuntu, không chạy trong PowerShell.

```bash
git clone https://github.com/HaUI-Libre/dx-lab.git
cd dx-lab
make env                  # tạo .env với khoá ngẫu nhiên; KHÔNG commit file này
make up                   # dựng service và ứng dụng, chờ healthy rồi deploy BPMN nếu thay đổi
make smoke                # kiểm tra gateway, claim/UUID, BPMN, tệp, vòng đời ticket, SSO
```

`make env` chép `.env.example` thành `.env` và thay mọi giá trị `changeme` bằng chuỗi
ngẫu nhiên, trừ `DEMO_USER_PASSWORD` (mật khẩu chung của tài khoản demo, giữ `changeme`).
Nếu tự chép bằng `cp`, phải đổi ít nhất `DATA_WORKFLOW_KEY`; `make up` dừng khi khoá
này còn là `changeme`.

Lần đầu chạy mất vài phút để tải image và dựng image `app` từ mã nguồn; sau khi sửa
mã trong `app/` thì chạy `docker compose build app` trước `make up`. `make help` liệt kê các lệnh khác.
Máy đã có volume PostgreSQL từ trước khi đổi sang image PostGIS (#76) thì script khởi
tạo không chạy lại; bật extension một lần bằng
`make psql DB=dxdata` rồi `CREATE EXTENSION IF NOT EXISTS postgis;`.
`docker compose down -v` xoá toàn bộ dữ liệu (database, tệp, realm). Mật khẩu
database chỉ được tạo ở lần chạy đầu, nên nếu đổi mật khẩu trong `.env` sau đó thì
phải `docker compose down -v` rồi `make up` lại.

| Service | Địa chỉ trên máy | Ghi chú |
|---|---|---|
| DX-Helpdesk (Nuxt 4) | http://localhost:3000 | Ứng dụng; đổi cổng bằng `APP_PORT` |
| API Gateway (APISIX) | http://localhost:9080 | Cửa vào duy nhất cho Tầng 2/3 |
| Keycloak | http://localhost:8080 | Đăng nhập, admin console tại `/admin` |
| PostgreSQL | `localhost:5432` | Chỉ để phát triển; `make psql` |
| Flowable, SeaweedFS | không mở ra ngoài | Chỉ gọi qua gateway |

Mọi cổng chỉ mở trên `127.0.0.1`.

### Profile Compose

| Profile | Service | Lệnh |
|---|---|---|
| mặc định | postgres, keycloak, apisix, flowable, seaweedfs, data-api, app | `make up` |
| `integration` | Snipe-IT, MariaDB, dịch vụ tích hợp tài sản (#71, #72); NATS ở M3 | `make demo` |
| `monitoring` | Prometheus, Grafana (M3) | `make demo` |
| `setup` | workflow-deploy, chạy một lần để deploy BPMN | `make up` và `make demo` tự gọi |

`make up` chỉ dựng profile mặc định để chạy nhẹ trên máy cấu hình vừa phải. `make demo`
bật thêm `integration` và `monitoring`. `make down` và `make ps` gồm cả service của mọi
profile. Service mặc định không phụ thuộc service của profile khác, nên tắt `integration`
thì ứng dụng vẫn chạy, chỉ thiếu dữ liệu từ hệ thống tài sản.

## Tài khoản demo

Tạo tự động khi Keycloak khởi tạo lần đầu, mật khẩu chung là `DEMO_USER_PASSWORD` trong `.env`.

| Username | Vai trò | Cơ sở | UUID |
|---|---|---|---|
| `sinhvien` | `ROLE_STUDENT` | — | `e90585fa-96ac-5f81-87a3-f817cc6d4323` |
| `kythuatvien` | `ROLE_TECHNICIAN` | CS1 | `9f19d880-973b-592b-bdb3-a354ac11cd6a` |
| `truongphong` | `ROLE_LAB_MANAGER` | CS1 | `d8608553-a02a-50b8-b05f-6cfe42da7850` |
| `quantri` | `ROLE_ADMIN` | — | `7d3ff8eb-0b1b-55a6-9dcd-8197344c83e2` |
| `sinhvien_cs2` | `ROLE_STUDENT` | — | `2324827d-3d37-5241-997f-25b64722818d` |
| `kythuatvien_cs2` | `ROLE_TECHNICIAN` | CS2 | `18685db0-c1c9-5e08-97cd-fdd20f23f6ed` |
| `truongphong_cs2` | `ROLE_LAB_MANAGER` | CS2 | `8fe64e2b-4772-5d63-ad4d-f48698f6b58e` |
| `sinhvien_cs3` | `ROLE_STUDENT` | — | `a7e3965a-b5b0-5a1f-b755-8f0f9130895b` |
| `kythuatvien_cs3` | `ROLE_TECHNICIAN` | CS3 | `b8074364-5be8-55e6-9106-a68702cbde00` |
| `truongphong_cs3` | `ROLE_LAB_MANAGER` | CS3 | `58ab5e48-abac-5e8e-8336-feb7e3e18a9e` |

Đăng nhập tại http://localhost:3000. Lấy token và gọi API bằng curl: xem
[core/identity/README.md](core/identity/README.md).
Ba kịch bản quy trình qua gateway: [docs/workflow-api.md](docs/workflow-api.md).

## API qua gateway

| Route | Trạng thái |
|---|---|
| `GET /api/me` | Đã chạy: thông tin người dùng, vai trò và cơ sở (`co_so`) từ token |
| `/api/files/*` | Đã chạy: tải lên, tải về tệp ([core/storage](core/storage/README.md)) |
| `GET /api/workflow/repository/process-definitions` | Đã chạy ([core/workflow](core/workflow/README.md)) |
| `/api/workflow/runtime/*`, `/api/workflow/history/*` | Route kiểm thử BPMN chỉ cho `ROLE_ADMIN`; `scripts/test-workflow-api.sh` chạy ba nhánh trong CI |
| `/api/data/tickets*` | CRUD bản nháp, chuyển trạng thái Flowable (#20), lịch sử/provenance và đánh giá (#21), tệp đính kèm (#26); Swagger tại `/api/data/docs`, [hợp đồng](data/openapi.yaml) |
| `/api/data/locations`, `/api/data/technicians` | Danh mục vị trí cho form báo hỏng; kỹ thuật viên cùng cơ sở cho trưởng phòng phân công (#26) |
| `/api/ai/*` | *(sắp có)* |
| `/api/assets/*` | *(sắp có, M2)*: thiết bị của người dùng lấy từ hệ thống tài sản |

Chi tiết xác thực và phân quyền: [core/gateway/README.md](core/gateway/README.md).

## Thành phần nguồn mở và giấy phép

Bảng thành phần, phiên bản, giấy phép và cách dùng: [docs/dependencies.md](docs/dependencies.md).

## Đóng góp

Đọc [CONTRIBUTING.md](CONTRIBUTING.md). Báo lỗi và đề xuất tính năng qua
[Issues](https://github.com/HaUI-Libre/dx-lab/issues).

## Giấy phép

Mã nguồn, cấu hình và tài liệu của DX-Lab phát hành theo
[Apache License 2.0](LICENSE). Đội chọn giấy phép này để trường hoặc đơn vị khác có
thể lấy nền tảng về, tích hợp với hệ thống sẵn có của họ và dùng cả cho mục đích
thương mại mà không bị buộc mở mã phần của họ; đồng thời người đóng góp được bảo vệ
bằng điều khoản cấp quyền sáng chế.

Người phân phối lại phải kèm giấy phép và tệp [NOTICE](NOTICE), giữ thông báo bản
quyền và ghi rõ tệp đã sửa. Phần mềm cung cấp nguyên trạng, không bảo hành.

- [LICENSE](LICENSE): toàn văn giấy phép
- [NOTICE](NOTICE): thông báo bản quyền và thành phần bên thứ ba
- [docs/license-decision.md](docs/license-decision.md): lý do chọn, quyền và nghĩa vụ,
  rà soát giấy phép từng thành phần

Mỗi tệp mang header SPDX; tệp không chứa được comment (JSON, ảnh) có tệp
`<tên-tệp>.license` nằm cạnh. CI kiểm tra bằng `reuse lint`.

<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# DX-Lab HaUI – Trạm điều hành số trên nền tảng DX-OS Open-Core

[![CI](https://github.com/HaUI-Libre/dx-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/HaUI-Libre/dx-lab/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

## Tính năng

DX-Helpdesk là ứng dụng minh họa: báo hỏng và sửa chữa thiết bị CNTT ở 3 cơ sở, nối với
phần mềm quản lý tài sản có sẵn của khách hàng (giả lập bằng Snipe-IT).

| Chức năng | Trạng thái |
|---|---|
| Đăng nhập SSO một lần cho mọi vai trò (Keycloak, OIDC) | Đã chạy |
| "Thiết bị của tôi" lấy từ hệ thống tài sản; báo hỏng kèm ảnh; báo theo vị trí khi hệ thống tài sản tắt | Đã chạy (#26, #72) |
| Định tuyến ticket về cơ sở theo vị trí thiết bị đã xác minh | Đã chạy (#73) |
| Quy trình BPMN: tiếp nhận, từ chối có lý do, phân công kỹ thuật viên cùng cơ sở, xử lý, nghiệm thu, mở lại có lý do | Đã chạy (#18, #20, #26) |
| Cập nhật nhãn tài sản trên Snipe-IT khi sửa và khi đóng, qua sự kiện NATS, không mất khi dịch vụ tích hợp dừng | Đã chạy (#72, #77) |
| Lịch sử và provenance từng ticket | Đã chạy (#21) |
| Portal: hồ sơ, nhóm, tài liệu hướng dẫn phân quyền theo thư mục | Đã chạy (#25, #95) |
| Giám sát vận hành bằng Prometheus và Grafana | Đã chạy (#78) |
| Gợi ý loại sự cố và mức ưu tiên trên form báo hỏng | Đã có giao diện và dịch vụ phân loại qua gateway (#28, #30, #31) |
| Thống kê theo cơ sở cho trưởng phòng | Đã chạy: `GET /api/data/stats` lọc theo cơ sở trong token (#22), trang `/dashboard` (#27) |

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
│   Dữ liệu cấu trúc (PostgreSQL + PostGIS) · Phi cấu trúc (SeaweedFS)│
│   Workflow (Flowable) · Trục sự kiện (NATS JetStream)             │
└──────────────────────────────────────────────────────────────────┘
  Ngoài DX-OS: hệ thống tài sản của khách hàng (Snipe-IT + MariaDB)
  Vận hành: Prometheus, Grafana
```

Nguyên tắc: **mọi lời gọi từ Tầng 2/3 đều đi qua API Gateway**, được xác thực
bằng token do Keycloak cấp. Đổi ứng dụng nghiệp vụ không cần sửa Open-Core.

Chi tiết: [docs/architecture.md](docs/architecture.md), gồm ánh xạ 7 lớp công nghệ của
đề và các quyết định kiến trúc (ADR).

### Tích hợp hệ thống tài sản của khách hàng

Snipe-IT và MariaDB đóng vai phần mềm quản lý tài sản mà trường đang dùng, chạy riêng
ngoài DX-OS. Chỉ dịch vụ tích hợp `asset-sync` (Tầng 2) gọi REST API `/api/v1` của
Snipe-IT bằng token riêng; không dịch vụ nào đọc MariaDB và DX-Lab không sửa mã
Snipe-IT. Thay Snipe-IT bằng phần mềm khác chỉ cần viết lại adapter trong
`integration/assets/`. Chi tiết: [integration/assets/README.md](integration/assets/README.md).

### Chuẩn mở

| Chuẩn | Dùng ở đâu |
|---|---|
| OpenID Connect, OAuth 2.0 (PKCE) | Đăng nhập SSO, token cho mọi API (Keycloak, APISIX, Nuxt) |
| BPMN 2.0 | Mô hình quy trình sửa chữa, chạy trên Flowable (`core/workflow/`) |
| OpenAPI 3 | Hợp đồng Data API (`data/openapi.yaml`), Swagger tại `/api/data/docs` |
| GeoJSON | Vùng và tọa độ 3 cơ sở trong dữ liệu mẫu (`data/samples/campuses.json`) |
| Prometheus exposition format | Metric của gateway, Keycloak, Data API, dịch vụ tích hợp |
| SPDX, REUSE 3.3 | Thông tin bản quyền, giấy phép trên từng tệp |

## Cấu trúc thư mục

| Thư mục | Nội dung | Phụ trách |
|---|---|---|
| `core/` | Cấu hình Open-Core: identity, gateway, workflow, storage | Trung |
| `data/` | Data API (FastAPI), schema, dữ liệu mẫu | Nam Anh |
| `ai/` | Dịch vụ Intelligence: phân loại, gợi ý mức ưu tiên | Nam Anh |
| `app/` | Giao diện H-P-D-I và ứng dụng DX-Helpdesk (Nuxt 4) | Trung |
| `integration/` | Dịch vụ tích hợp tài sản `asset-sync` (adapter Snipe-IT) | Nam Anh |
| `docs/` | Kiến trúc, quy trình BPMN, bảng license, báo cáo | Linh |
| `scripts/` | Script tiện ích và kiểm thử trên stack thật (smoke, seed…) | Cả đội |
| `tests/` | Test Python chạy không cần stack (`make test`) | Cả đội |

## Cài đặt và chạy

Yêu cầu, toàn bộ là phần mềm nguồn mở:

- [Docker Engine](https://docs.docker.com/engine/install/) 24+ (Apache-2.0) và
  [Docker Compose plugin](https://docs.docker.com/compose/install/linux/) v2.17+ (Apache-2.0)
- Git, `make`, `curl`, `bash`, Python 3 (thư viện chuẩn)
- Khuyến nghị 16 GB RAM

Không cần Docker Desktop. Docker Desktop không phải phần mềm nguồn mở
(xem [docs/license-decision.md](docs/license-decision.md)).

Build app DX-Helpdesk và plugin APISIX từ mã nguồn rồi chạy ngoài repo, không dùng
Docker: [docs/build-from-source.md](docs/build-from-source.md).

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
| Snipe-IT | http://127.0.0.1:8081 | Profile `integration`; tài khoản `SNIPEIT_ADMIN_USER` / `SNIPEIT_ADMIN_PASSWORD` |
| Grafana | http://127.0.0.1:3001 | Profile `monitoring`; tài khoản `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD` |
| Flowable, SeaweedFS, NATS, Prometheus, MariaDB | không mở ra ngoài | Chỉ gọi trong mạng Docker hoặc qua gateway |

Mọi cổng chỉ mở trên `127.0.0.1`.

### Profile Compose

| Profile | Service | Lệnh |
|---|---|---|
| mặc định | postgres, keycloak, apisix, flowable, seaweedfs, data-api, app | `make up` |
| `integration` | Snipe-IT, MariaDB, dịch vụ tích hợp tài sản, NATS JetStream (#71, #72, #77) | `make demo` |
| `monitoring` | Prometheus, Grafana tại `127.0.0.1:3001`, exporter PostgreSQL và NATS (#78, [core/monitoring](core/monitoring/README.md)) | `make demo` |
| `setup` | workflow-deploy, chạy một lần để deploy BPMN | `make up` và `make demo` tự gọi |

`make up` chỉ dựng profile mặc định để chạy nhẹ trên máy cấu hình vừa phải. `make demo`
bật thêm `integration` và `monitoring`. `make down` và `make ps` gồm cả service của mọi
profile. Service mặc định không phụ thuộc service của profile khác, nên tắt `integration`
thì ứng dụng vẫn chạy, chỉ thiếu dữ liệu từ hệ thống tài sản.
Sau `make demo`, chạy `make smoke-assets` để kiểm tra thiết bị của `sinhvien` và
việc trả nhãn Snipe-IT về trạng thái ban đầu khi đóng ticket.

### Cấu hình

Mọi tham số nằm trong `.env` (tạo bằng `make env`); `.env.example` liệt kê đủ biến với
giá trị giả. Nhóm chính:

| Nhóm | Biến | Ghi chú |
|---|---|---|
| Cổng trên máy | `APP_PORT`, `GATEWAY_PORT`, `KEYCLOAK_PORT`, `POSTGRES_PORT`, `SNIPEIT_PORT`, `GRAFANA_PORT` | Mọi cổng bind `127.0.0.1` |
| Mật khẩu, khoá | `*_PASSWORD`, `*_SECRET`, `DATA_WORKFLOW_KEY`, `DATA_ASSET_KEY` | `make env` sinh ngẫu nhiên; trừ `DEMO_USER_PASSWORD` |
| Tích hợp tài sản | `ASSET_REPAIR_LABEL`, `ASSET_SITE_ROOTS`, `SNIPEIT_API_URL`, `NATS_URL` | Đổi khi nối với hệ thống tài sản khác |
| Demo | `DEMO_LOGIN_HINTS` | Mặc định `false`; `make demo` bật `true` để trang đăng nhập có nút vào thử theo vai trò, chỉ điền sẵn tên qua `login_hint` |

### Kiểm tra

| Lệnh | Kiểm tra |
|---|---|
| `make check` | Giấy phép từng tệp theo REUSE (`reuse lint`) |
| `make test` | Test Python trong `tests/` (Data API, provenance, deploy BPMN, adapter Snipe-IT, sự kiện NATS) |
| `make smoke` | Trên stack đang chạy: token và `co_so`, gateway 401/403/200, quyền tệp theo thư mục, vòng đời ticket có mở lại và từ chối, đăng nhập qua app, trang ticket theo vai trò |
| `make smoke-assets` | Sau `make demo`: thiết bị từ Snipe-IT, nhãn sửa chữa và hoàn trả, đóng ticket khi `asset-sync` dừng, sự kiện thời gian thực qua SSE chỉ tới đúng trưởng phòng |
| `make smoke-monitoring` | Sau `make demo` và `make smoke`: dashboard Grafana và số liệu thật của gateway, database |

CI chạy `REUSE lint`, `Secret scan (gitleaks)`, `PR title`, `Python tests` và
`Stack từ volume trống` (dựng toàn bộ stack trên máy sạch rồi chạy `make smoke`) cho mọi
PR; cả năm là check bắt buộc trước khi merge.

### Xử lý sự cố

| Hiện tượng | Nguyên nhân | Cách xử lý |
|---|---|---|
| Gateway trả 502 sau khi build lại một container (`docker compose build data-api` rồi `up -d`) | Container mới nhận IP khác; APISIX vẫn giữ IP cũ trong bộ nhớ đệm DNS | `docker compose restart apisix` |
| Header hiện "Mất kết nối cập nhật" | Profile `integration` tắt nên không có NATS; trang vẫn chạy, chỉ không tự cập nhật | Chạy `make demo` hoặc bật profile `integration` |
| Trang đăng nhập không có nút vào thử | `DEMO_LOGIN_HINTS=false` (mặc định của `make up`) | Chạy `make demo` |

## Chạy thử

Dựng đủ các phần (lõi, hệ thống tài sản Snipe-IT, giám sát) rồi nạp dữ liệu mẫu:

```bash
make env      # chỉ cần ở lần đầu
make demo     # mọi profile; trang đăng nhập có nút vào thử theo vai trò
make seed     # phiếu mẫu, tài liệu hướng dẫn mẫu
```

Mở http://localhost:3000. Mật khẩu chung của các tài khoản là giá trị `DEMO_USER_PASSWORD`
(xem `.env.example`).

| Vai trò | Tên đăng nhập | Làm gì |
|---|---|---|
| Sinh viên | `sinhvien` | Báo hỏng, theo dõi phiếu của mình, đánh giá sau khi đóng |
| Trưởng phòng lab cơ sở 1 | `truongphong` | Tiếp nhận hoặc từ chối, phân công, nghiệm thu, mở lại |
| Kỹ thuật viên cơ sở 1 | `kythuatvien` | Nhận việc, lập biên bản, đánh dấu hoàn thành |
| Quản trị | `quantri` | Xem cả ba cơ sở |

Mỗi vai trò nên dùng một trình duyệt hoặc một hồ sơ trình duyệt riêng; các cửa sổ ẩn danh của
cùng một trình duyệt dùng chung phiên đăng nhập.

### Một vòng nghiệp vụ mẫu

1. **Sinh viên báo hỏng.** Vào *Báo hỏng*, chọn thiết bị `HAUI-LT-0001` (lấy từ Snipe-IT),
   nhập tiêu đề và mô tả, thêm ảnh nếu có. Khi mô tả có từ 15 ký tự, gợi ý loại sự cố và
   mức ưu tiên hiện ra kèm từ khoá; bấm *Dùng gợi ý* nếu đồng ý, rồi *Gửi yêu cầu*. Màn hình
   hiện mã phiếu mới. Trưởng phòng vẫn chốt mức ưu tiên khi phân công.
2. **Trưởng phòng tiếp nhận.** Phiếu xuất hiện trong *Hàng đợi CS1*. Mở phiếu, bấm
   *Tiếp nhận*, chọn kỹ thuật viên cùng cơ sở rồi *Phân công*.
3. **Kỹ thuật viên xử lý.** Phiếu có trong *Việc của tôi*. Bấm *Nhận việc*: thiết bị trên
   Snipe-IT (http://127.0.0.1:8081) chuyển nhãn "Đang sửa chữa". Ghi *Biên bản xử lý* rồi
   *Đánh dấu hoàn thành*.
4. **Trưởng phòng nghiệm thu.** Bấm *Nghiệm thu và đóng*: Snipe-IT trả lại nhãn ban đầu và
   ghi số phiếu vào ghi chú của thiết bị.
5. **Sinh viên đánh giá.** Mở phiếu đã đóng, chọn mức độ hài lòng, *Gửi đánh giá*.

Nhánh khác của quy trình:

- *Từ chối* chỉ có ở bước tiếp nhận, *Mở lại* chỉ có ở bước nghiệm thu; cả hai bắt buộc nhập
  lý do. Mở lại giao phiếu về đúng kỹ thuật viên cũ.
- Hai cửa sổ cùng mở danh sách phiếu thì thay đổi ở cửa sổ này hiện ở cửa sổ kia sau vài
  giây (header ghi "Trực tiếp").
- Chế độ xem *Cột* trong danh sách cho phép kéo phiếu sang bước kế tiếp; mỗi lần thả đi qua
  quy trình như nút trên trang chi tiết.
- Ctrl+K mở bảng lệnh: chuyển trang, đổi chế độ sáng tối, mở phiếu theo mã.
- Số liệu vận hành (request qua gateway, bước quy trình, cập nhật tài sản) xem trên Grafana
  (http://127.0.0.1:3001). Số liệu phiếu theo cơ sở xem ở trang *Thống kê* trong ứng dụng.

Phiếu mẫu của `make seed` chỉ để xem; thao tác quy trình trên phiếu mẫu trả lỗi 409 vì chưa
gắn với quy trình. Hãy chạy vòng nghiệp vụ trên phiếu mới tạo.

## Tài khoản demo

Tạo tự động khi Keycloak khởi tạo lần đầu, mật khẩu chung là `DEMO_USER_PASSWORD` trong `.env`.
`make demo` chạy với `DEMO_LOGIN_HINTS=true`: trang đăng nhập có nút vào thử cho sinh viên,
trưởng phòng, kỹ thuật viên và quản trị. Nút chỉ điền sẵn tên đăng nhập qua `login_hint`,
mật khẩu vẫn nhập trên Keycloak. `make up` giữ giá trị trong `.env` (mặc định `false`), nên
nút không hiện ngoài buổi demo.

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
| `/api/data/stats` | Thống kê cho trưởng phòng (cơ sở trong token) và admin (mọi cơ sở hoặc `?co_so=`): theo trạng thái, loại, cơ sở, giờ xử lý trung bình, số quá hạn, số lần mở lại (#22) |
| `/api/ai/*` | Dịch vụ phân loại mặc định: `POST /api/ai/classify` có xác thực, gợi ý theo mô hình hoặc luật dự phòng (#28, #30, #31) |
| `/api/assets/*` | Dịch vụ tích hợp profile `integration` (#72): thiết bị của người dùng, tra mã và vị trí, cập nhật nhãn tài sản; profile tắt thì route trả lỗi dịch vụ |

Chi tiết xác thực và phân quyền: [core/gateway/README.md](core/gateway/README.md).

## Thành phần nguồn mở và giấy phép

Bảng thành phần, phiên bản, giấy phép và cách dùng: [docs/dependencies.md](docs/dependencies.md).

## Đóng góp

Đọc [CONTRIBUTING.md](CONTRIBUTING.md). Báo lỗi và đề xuất tính năng qua
[Issues](https://github.com/HaUI-Libre/dx-lab/issues). Việc dự kiến làm tiếp ở
[ROADMAP.md](ROADMAP.md); người mới bắt đầu từ Issue có nhãn
[`good first issue`](https://github.com/HaUI-Libre/dx-lab/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22).

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

## Bối cảnh

Dự án khởi đầu tại Olympic Phần mềm nguồn mở 2026, chủ đề DX-OS Open-Core.

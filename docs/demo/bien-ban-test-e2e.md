<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Biên bản kiểm thử End-to-End theo chuỗi demo tích hợp (Milestone M3.28)

**Tham chiếu Issue:** [#34](https://github.com/HaUI-Libre/dx-lab/issues/34)  
**Phụ thuộc:** [#32](https://github.com/HaUI-Libre/dx-lab/issues/32) (M3.26)  
**Tài liệu liên quan:** `docs/usecases.md`, `docs/architecture.md`, `docs/manual-checks.md`, `docs/testing.md`  
**Ngày thực hiện:** 25/10/2026  
**Môi trường kiểm thử:** Stack đầy đủ khởi động bằng `make demo` (bao gồm lõi Open-Core, profile `integration` và profile `monitoring`).  
**Lệnh chạy kiểm thử tự động:** `make test-e2e` (hoặc `python3 scripts/test-demo-e2e.py`).

---

## 1. Mục tiêu và điều kiện hoàn thành

- **Mục tiêu:** Kiểm thử thực tế như Hội đồng sẽ xem theo chuỗi demo tích hợp và toàn bộ các nhánh rẽ nghiệp vụ, bảo đảm tính ổn định tuyệt đối trước buổi báo cáo.
- **Điều kiện hoàn thành:** Chạy toàn bộ kịch bản kiểm thử 2 lần liên tiếp không phát sinh lỗi (0 failed checks).

---

## 2. Kết quả tổng hợp

| Lần chạy | Lệnh thực hiện | Số ca kiểm thử | Kết quả | Trạng thái |
|:---:|:---|:---:|:---:|:---:|
| **Lần 1 (Run 1)** | `make test-e2e` | 28 / 28 checks | 28 ĐẠT, 0 LỖI | **PASS** |
| **Lần 2 (Run 2)** | `make test-e2e` | 28 / 28 checks | 28 ĐẠT, 0 LỖI | **PASS** |

Hệ thống hoàn thành điều kiện nghiệm thu của Issue #34: **ĐẠT 2 LẦN LIÊN TIẾP KHÔNG LỖI**.

---

## 3. Chi tiết kiểm thử chuỗi chính (Main Demo Chain)

Chuỗi chính mô phỏng luồng nghiệp vụ hoàn chỉnh giữa Sinh viên, Trưởng phòng lab, Kỹ thuật viên, hệ thống quản lý tài sản Snipe-IT của khách hàng và các dịch vụ nền tảng:

### Bước 1: Đăng nhập SSO (OIDC / Keycloak)
- **Hành động:** Xác thực 4 vai trò qua `GET /api/me` với token OIDC tương ứng:
  - `sinhvien` (`ROLE_STUDENT`)
  - `truongphong` (`ROLE_LAB_MANAGER`, `co_so=CS1`)
  - `kythuatvien` (`ROLE_TECHNICIAN`, `co_so=CS1`)
  - `quantri` (`ROLE_ADMIN`)
- **Kết quả:** Gateway trả về đúng thông tin định danh `sub`, `username`, danh sách vai trò và thuộc tính `co_so`.

### Bước 2: Thiết bị của tôi (Tích hợp Snipe-IT)
- **Hành động:** `sinhvien` gọi `GET /api/assets/me` qua API Gateway. Tra cứu chi tiết tài sản qua `GET /api/assets/bytag/{tag}` và `GET /api/assets/locations/{location_id}/assets`.
- **Kết quả:** Lấy được đúng thiết bị giao cho sinh viên (`HAUI-LT-0001`, `id=1`, `location_id=4`). Nhãn trạng thái ban đầu trên Snipe-IT là "Sẵn sàng" (`Ready`).

### Bước 3: Gợi ý phân loại AI & Fallback
- **Hành động:** Gửi mô tả báo hỏng tới `POST /api/ai/classify` qua Gateway.
- **Kết quả:** Endpoint phản hồi gợi ý phân loại; khi dịch vụ AI offline, cơ chế fallback xử lý linh hoạt, không chặn quy trình báo hỏng (tuân thủ ADR-05).

### Bước 4: Tạo bản nháp và tải ảnh lỗi lên SeaweedFS
- **Hành động:**
  - Tạo ticket nháp qua `POST /api/data/tickets` -> trạng thái `DRAFT`.
  - Tải ảnh lỗi PNG lên bucket SeaweedFS qua `PUT /api/files/tickets/{tid}/screen-error.png`.
  - Đăng ký metadata ảnh qua `POST /api/data/tickets/{tid}/attachments`.
- **Kết quả:** Tệp được lưu trữ độc lập trên SeaweedFS, kiểm tra chống giả mạo đường dẫn và gắn chặt với ticket.

### Bước 5: Gửi ticket và định tuyến theo cơ sở
- **Hành động:** Sinh viên gửi ticket qua `POST /api/data/tickets/{tid}/actions/submit`.
- **Kết quả:** Data API xác minh vị trí từ Snipe-IT, định tuyến ticket về đúng cơ sở `CS1`, khởi tạo quy trình BPMN `dxlabHelpdeskRepair` trên Flowable. Trạng thái chuyển thành `SUBMITTED`.

### Bước 6: Phân quyền hàng đợi theo cơ sở
- **Hành động:** Trưởng phòng cơ sở 2 (`truongphong_cs2`) cố tình truy cập hoặc tiếp nhận ticket của CS1.
- **Kết quả:** Bị Data API chặn với mã `404 Not Found` (lọc hàng đợi theo claim `co_so` trong JWT, không tin tham số client).

### Bước 7: Tiếp nhận và phân công kỹ thuật viên
- **Hành động:**
  - `truongphong` (CS1) tiếp nhận ticket qua `POST /actions/accept`.
  - `truongphong` lấy danh sách kỹ thuật viên (`GET /api/data/technicians` - chỉ trả về KTV cơ sở CS1).
  - Thử gán cho kỹ thuật viên CS2 -> bị chặn với mã `422 Unprocessable Entity`.
  - Gán cho `kythuatvien` CS1 qua `POST /actions/assign`.
- **Kết quả:** Ticket chuyển trạng thái sang `ASSIGNED`.

### Bước 8: Kỹ thuật viên nhận việc & Cập nhật Snipe-IT
- **Hành động:** `kythuatvien` gọi `POST /actions/start`.
- **Kết quả:**
  - Ticket chuyển trạng thái sang `IN_PROGRESS`.
  - Data API phát sự kiện `dxlab.ticket.status_changed` lên NATS JetStream.
  - Dịch vụ `asset-sync` nhận sự kiện và gọi Snipe-IT REST API đổi nhãn trạng thái tài sản thành `"Đang sửa chữa"`.

### Bước 9: Xử lý và lập biên bản
- **Hành động:**
  - Kỹ thuật viên hoàn thành thiếu biên bản -> bị chặn với mã `422 Unprocessable Entity`.
  - Kỹ thuật viên gửi biên bản sửa chữa hợp lệ qua `POST /actions/resolve`.
- **Kết quả:** Ticket chuyển trạng thái sang `RESOLVED`.

### Bước 10: Nhánh mở lại tại bước nghiệm thu
- **Hành động:**
  - Trưởng phòng mở lại nhưng không nhập lý do -> bị chặn với mã `422 Unprocessable Entity`.
  - Trưởng phòng mở lại kèm lý do qua `POST /actions/reopen`.
- **Kết quả:** Ticket quay về trạng thái `IN_PROGRESS`, tự động giao lại đúng kỹ thuật viên cũ. Lịch sử ticket ghi nhận hành động `REOPEN`.
- **Khắc phục lần 2:** Kỹ thuật viên bổ sung biên bản và hoàn thành lần 2 -> chuyển sang `RESOLVED`.

### Bước 11: Nghiệm thu, đóng ticket và hoàn trả tài sản
- **Hành động:** Trưởng phòng nghiệm thu và đóng ticket qua `POST /actions/close`.
- **Kết quả:**
  - Ticket chuyển trạng thái sang `CLOSED`.
  - Snipe-IT nhận sự kiện qua NATS, tự động hoàn trả nhãn ban đầu ("Sẵn sàng") và cập nhật ghi chú tài sản kèm mã ticket.

### Bước 12: Đánh giá chất lượng & Kiểm tra Provenance
- **Hành động:** Sinh viên đánh giá 5 sao qua `PUT /api/data/tickets/{tid}/rating`. Kiểm tra lịch sử kiểm toán qua `GET /api/data/tickets/{tid}/provenance`.
- **Kết quả:**
  - Đầy đủ 11 sự kiện nghiệp vụ: `CREATE_DRAFT`, `ATTACH`, `SUBMIT`, `ACCEPT`, `ASSIGN`, `START_PROGRESS`, `RESOLVE`, `REOPEN`, `RESOLVE`, `CLOSE`, `RATE`.
  - Thuộc tính `reopen_count = 1`.

### Bước 13: Thống kê & Giám sát vận hành
- **Hành động:**
  - Sinh viên truy cập `GET /api/data/stats` -> bị chặn `403 Forbidden`.
  - Trưởng phòng truy cập `GET /api/data/stats` -> gateway cấp quyền thành công.
  - Kiểm tra trạng thái Grafana (`/api/health`) và Prometheus metrics (`apisix_http_status`, `dxlab_ticket_transitions_total`, `pg_stat_activity_count`).
- **Kết quả:** Số liệu đếm request và đếm bước chuyển trạng thái quy trình ghi nhận số liệu thực tế.

---

## 4. Chi tiết kiểm thử các nhánh phụ (Branch Scenarios)

| Nhánh phụ | Tình huống kiểm thử | Kết quả mong đợi | Kết quả thực tế |
|---|---|---|:---:|
| **Nhánh 1: Từ chối** | Trưởng phòng từ chối ở bước tiếp nhận | Thiếu lý do bị chặn 422; có lý do chuyển sang `REJECTED`, Flowable kết thúc, Snipe-IT không bị sửa đổi | **ĐẠT** |
| **Nhánh 2: Không có asset_id** | Báo hỏng thiết bị phòng lab không có ID tài sản trên Snipe-IT (hoặc profile integration tắt) | Người dùng chọn vị trí thủ công, nhập mã máy vào mô tả, ticket gửi và xử lý bình thường | **ĐẠT** |
| **Nhánh 3: AI Fallback** | Dịch vụ AI offline hoặc không phản hồi | Endpoint AI trả mã lỗi phù hợp, không gây gián đoạn Gateway, không chặn luồng gửi ticket | **ĐẠT** |
| **Nhánh 4: Tích hợp ngoại tuyến** | Đóng ticket khi dịch vụ `asset-sync` đang tắt (kiểm chứng ở `test-assets-api.py`) | NATS JetStream giữ sự kiện trên hàng đợi bền vững; khi `asset-sync` khởi động lại, nhãn Snipe-IT vẫn được cập nhật | **ĐẠT** |

---

## 5. Đánh giá lỗi (Bug Report)

- **Lỗi chặn quy trình (Blocker):** 0
- **Lỗi chức năng (Major/Minor):** 0
- **Ghi chú vận hành:**
  - Khi khởi động toàn bộ stack lần đầu từ máy sạch (`make demo`), cần để Keycloak và PostgreSQL hoàn tất chu kỳ health check trước khi gửi request hàng loạt. Cơ chế retry trong `test-demo-e2e.py` bảo đảm kiểm thử tự động luôn ổn định.
  - Tính năng dashboard thống kê nâng cao (`/api/data/stats`) được bảo vệ quyền truy cập chính xác ở tầng API Gateway (chỉ `ROLE_LAB_MANAGER` và `ROLE_ADMIN`).

---

## 6. Kết luận

Toàn bộ chuỗi demo tích hợp và các nhánh rẽ nghiệp vụ đã được kiểm chứng hoạt động hoàn hảo, đáp ứng 100% yêu cầu nghiệm thu của Issue [#34](https://github.com/HaUI-Libre/dx-lab/issues/34). Dự án sẵn sàng cho bước chuẩn bị kịch bản diễn tập và bảo vệ trước Hội đồng (Milestone D.36).

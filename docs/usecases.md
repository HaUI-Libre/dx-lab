<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Đặc tả nghiệp vụ DX-Helpdesk

DX-Helpdesk là ứng dụng Tầng 3: tiếp nhận và xử lý yêu cầu hỗ trợ CNTT, thiết bị
trong phòng lab. Ứng dụng không tự lưu dữ liệu hay tự quản lý người dùng mà dùng
các dịch vụ của tầng dưới, mọi lời gọi đi qua API Gateway.

## 1. Vị trí trong kiến trúc

**Tầng 1 – Open-Core (headless).** Các dịch vụ dùng chung, gọi qua APISIX:

- Keycloak: đăng nhập SSO (OIDC), quản lý người dùng và vai trò.
- Flowable: chạy quy trình xử lý yêu cầu theo BPMN 2.0.
- PostgreSQL: dữ liệu có cấu trúc.
- SeaweedFS: tệp đính kèm.

**Tầng 2 – H-P-D-I.**

| Không gian | Dùng cho DX-Helpdesk |
|---|---|
| H – Con người | Tài khoản, phòng ban/phòng máy, phân quyền theo vai trò, SSO |
| P – Quy trình | Trạng thái ticket, phân công, hàng đợi công việc, lịch sử xử lý |
| D – Dữ liệu | Dữ liệu ticket kèm metadata/provenance, Data API (FastAPI), số liệu cho dashboard |
| I – Trí tuệ | Gợi ý loại sự cố và mức ưu tiên; người dùng xác nhận trước khi gửi; có bộ quy tắc dự phòng khi mô hình không chạy |

**Tầng 3 – DX-Helpdesk.** Giao diện người dùng cuối viết bằng Nuxt.

## 2. Vai trò và phân quyền

Có 4 realm role trong Keycloak:

**`ROLE_STUDENT` – Sinh viên, người dùng phòng lab.**
Đăng nhập, tạo ticket, theo dõi tiến độ và lịch sử ticket của mình, bổ sung thông
tin hoặc hủy ticket khi chưa được tiếp nhận.

**`ROLE_TECHNICIAN` – Kỹ thuật viên.**
Xem hàng đợi công việc của mình, cập nhật trạng thái xử lý, lập biên bản kiểm tra,
đề xuất thay vật tư/linh kiện.

**`ROLE_LAB_MANAGER` – Trưởng phòng lab.**
Phân loại ticket, phân công kỹ thuật viên, nghiệm thu, duyệt vật tư, xem dashboard.

**`ROLE_ADMIN` – Quản trị hệ thống.**
Quản lý tài khoản, gán vai trò trong Keycloak, quản lý danh mục, theo dõi kết nối
tới các dịch vụ Tầng 1.

### Ma trận phân quyền

| Chức năng | STUDENT | TECHNICIAN | LAB_MANAGER | ADMIN |
|---|:-:|:-:|:-:|:-:|
| Tạo và gửi ticket | Có | Có | Có | Có |
| Xem ticket của mình | Có | Có | Có | Có |
| Phân loại, phân công kỹ thuật viên | | | Có | |
| Tiếp nhận, cập nhật tiến độ | | Có | | |
| Lập biên bản, đề xuất vật tư | | Có | | |
| Nghiệm thu, đóng ticket | | | Có | |
| Xem dashboard | | | Có | Có |
| Quản trị hệ thống | | | | Có |

## 3. Loại sự cố và mức ưu tiên

Ticket lưu trong PostgreSQL, kèm các trường provenance: `source`, `created_by`,
`created_at`, `updated_at`.

### Loại sự cố (category)

Mã dùng chung với `data/schema.sql` và `data/openapi.yaml`.

| Mã | Ví dụ |
|---|---|
| `HARDWARE` – Phần cứng | Máy không lên nguồn, hỏng RAM, màn hình xanh; thiết bị ngoại vi, thiết bị mạng, máy chiếu, thiết bị đo |
| `SOFTWARE_ENVIRONMENT` – Phần mềm và môi trường | Lỗi hệ điều hành, bản quyền phần mềm chuyên ngành, cài đặt Docker/IDE/SDK |
| `NETWORK_ACCOUNT` – Mạng và tài khoản | Mất mạng LAN/VLAN, xin quyền truy cập máy chủ/VPN, cấp lại mật khẩu máy trạm |
| `LAB_ASSET` – Tài sản và đặt phòng | Mượn máy ngoài giờ, đăng ký bảo trì thiết bị nghiên cứu |

### Mức ưu tiên (priority)

| Mức | Khi nào |
|---|---|
| `URGENT` | Ảnh hưởng tới buổi thi trực tuyến hoặc buổi thực hành đông sinh viên |
| `HIGH` | Hỏng máy chủ lab hoặc thiết bị mạng trung tâm, nhiều người bị ảnh hưởng |
| `MEDIUM` | Lỗi trên một máy, người dùng tạm chuyển sang máy khác được |
| `LOW` | Đề nghị cài thêm phần mềm, góp ý cải thiện phòng lab |

## 4. Trạng thái ticket

Quy trình chạy trên Flowable, gọi qua gateway.

| Trạng thái | Ý nghĩa |
|---|---|
| `DRAFT` | Người dùng đang soạn, chưa gửi |
| `SUBMITTED` | Đã gửi; tạo process instance trên Flowable, ticket vào hàng đợi của trưởng phòng lab |
| `ASSIGNED` | Trưởng phòng lab đã giao cho một kỹ thuật viên |
| `IN_PROGRESS` | Kỹ thuật viên đã nhận và đang xử lý |
| `RESOLVED` | Kỹ thuật viên xử lý xong, đã lập biên bản, chờ nghiệm thu |
| `CLOSED` | Trưởng phòng lab nghiệm thu và đóng ticket; số liệu được tính vào dashboard |
| `REJECTED` | Trưởng phòng lab từ chối ticket không hợp lệ, người tạo nhận được lý do |

Luồng chính: `SUBMITTED`, `ASSIGNED`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`.
Nhánh từ chối: `SUBMITTED` sang `REJECTED`.

## 5. Kịch bản sử dụng

### Kịch bản 1: Sinh viên gửi yêu cầu

- **Người thực hiện:** sinh viên (`ROLE_STUDENT`).
- **Điều kiện:** đã đăng nhập qua Keycloak.

1. Vào portal, chọn "Gửi yêu cầu hỗ trợ mới".
2. Nhập tiêu đề ("Máy PC-04 phòng 301 không khởi động được"), mô tả, đính kèm ảnh
   lỗi. Ảnh được tải lên SeaweedFS qua `/api/files`.
3. Bấm gửi. Ticket được lưu qua Data API (`/api/data`) và quy trình được khởi tạo
   trên Flowable (`/api/workflow`).

**Kết quả:** ticket ở trạng thái `SUBMITTED`, nằm trong hàng đợi phân loại của
trưởng phòng lab.

### Kịch bản 2: Trưởng phòng lab phân loại và phân công

- **Người thực hiện:** trưởng phòng lab (`ROLE_LAB_MANAGER`).
- **Điều kiện:** có ticket `SUBMITTED`.

1. Mở hàng đợi công việc.
2. Mở ticket PC-04, chọn mức ưu tiên `HIGH`, giao cho kỹ thuật viên A.
3. Lệnh phân công đi qua APISIX, hoàn thành task trên Flowable, ticket chuyển sang
   `ASSIGNED`.

**Kết quả:** ticket hiện trong mục "Công việc của tôi" của kỹ thuật viên A.

### Kịch bản 3: Kỹ thuật viên xử lý và lập biên bản

- **Người thực hiện:** kỹ thuật viên (`ROLE_TECHNICIAN`).
- **Điều kiện:** ticket `ASSIGNED`.

1. Mở danh sách việc, chọn "Tiếp nhận xử lý". Ticket chuyển sang `IN_PROGRESS`.
2. Kiểm tra tại chỗ và sửa (thay cáp tín hiệu, kiểm tra kết nối mạng).
3. Nhập biên bản kết quả, bấm "Đánh dấu hoàn thành". Ticket chuyển sang `RESOLVED`.

**Kết quả:** ticket nằm trong hàng đợi chờ nghiệm thu của trưởng phòng lab.

### Kịch bản 4: Nghiệm thu và đóng ticket

- **Người thực hiện:** trưởng phòng lab (`ROLE_LAB_MANAGER`), sinh viên (`ROLE_STUDENT`).
- **Điều kiện:** ticket `RESOLVED`.

1. Trưởng phòng lab kiểm tra kết quả, chọn "Nghiệm thu và đóng".
2. Quy trình trên Flowable kết thúc, ticket chuyển sang `CLOSED`.
3. Sinh viên nhận thông báo và đánh giá mức độ hài lòng.
4. Số liệu được cộng vào API thống kê (`/api/data/stats`).

**Kết quả:** dashboard hiển thị thời gian xử lý so với SLA, số ticket đã xử lý và
tỷ lệ hài lòng.

### Kịch bản 5: Từ chối yêu cầu không hợp lệ

- **Người thực hiện:** trưởng phòng lab (`ROLE_LAB_MANAGER`).
- **Điều kiện:** ticket `SUBMITTED`.

1. Trưởng phòng lab thấy yêu cầu vi phạm nội quy phòng máy, ví dụ xin cài phần mềm
   không được phép.
2. Chọn "Từ chối" và ghi lý do.
3. Flowable đi theo nhánh từ chối, ticket chuyển sang `REJECTED` và quy trình kết thúc.

**Kết quả:** người tạo xem được ticket bị từ chối kèm lý do.

### Kịch bản 6: Gợi ý loại sự cố và mức ưu tiên

- **Người thực hiện:** sinh viên (`ROLE_STUDENT`), dịch vụ AI.
- **Điều kiện:** dịch vụ AI chạy sau gateway (`/api/ai`).

1. Sinh viên nhập mô tả: "Màn hình máy 12 bị chớp, có sọc tím, có mùi khét".
2. Giao diện gọi `POST /api/ai/classify` qua APISIX.
3. Mô hình phân loại đề xuất `HARDWARE`, `URGENT` và hiện các từ khóa dẫn tới kết
   quả.
4. Nếu mô hình không phản hồi, hệ thống dùng bộ quy tắc dự phòng dựa trên từ khóa
   ("mùi khét", "chớp").
5. Sinh viên xem gợi ý, giữ nguyên hoặc sửa, rồi mới gửi.

**Kết quả:** ticket có sẵn loại và mức ưu tiên khi gửi, trưởng phòng lab không phải
phân loại lại từ đầu.

<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Đặc tả nghiệp vụ DX-Helpdesk

DX-Helpdesk là ứng dụng Tầng 3 tiếp nhận và xử lý báo hỏng thiết bị CNTT, tích hợp
với phần mềm quản lý tài sản CNTT mà đơn vị (khách hàng) đang dùng. Người dùng đăng
nhập SSO, thấy thiết bị của mình lấy từ hệ thống tài sản, báo hỏng, ticket được định
tuyến tới kỹ thuật viên đúng cơ sở, và khi sửa xong trạng thái thiết bị được cập nhật
ngược về hệ thống tài sản.

Ứng dụng không tự lưu danh mục tài sản hay tự quản lý người dùng. Nó dùng dịch vụ của
các tầng dưới, mọi lời gọi đi qua API Gateway.

Trong bài dự thi, hệ thống tài sản của khách hàng được giả lập bằng
[Snipe-IT](https://snipeitapp.com) chạy như một dịch vụ riêng. Đơn vị mẫu là HaUI với
3 cơ sở, mã `CS1`, `CS2`, `CS3`.

Phần nào chưa triển khai được ghi rõ là dự kiến kèm milestone. Trạng thái thực tế từng
thành phần: [architecture.md](architecture.md) mục 8.

## 1. Vị trí trong kiến trúc

**Tầng 1 – Open-Core (headless).** Dịch vụ dùng chung, gọi qua APISIX:

- Keycloak: đăng nhập SSO (OIDC), vai trò, thuộc tính cơ sở `co_so` của người dùng.
- Flowable: quy trình sửa chữa theo BPMN 2.0.
- PostgreSQL: dữ liệu ticket; PostGIS cho vị trí _(dự kiến M3)_.
- SeaweedFS: ảnh và biên bản đính kèm.
- NATS: trục sự kiện tích hợp _(dự kiến M3)_.

**Tầng 2 – H-P-D-I.**

| Không gian | Dùng cho DX-Helpdesk |
|---|---|
| H – Con người | Tài khoản SSO, 4 vai trò, cơ sở làm việc của kỹ thuật viên và quản lý |
| P – Quy trình | Quy trình sửa chữa, định tuyến theo cơ sở, phân công, nghiệm thu, mở lại, lịch sử |
| D – Dữ liệu | Ticket kèm provenance, liên kết tới tài sản của khách hàng, số liệu theo cơ sở cho dashboard |
| I – Trí tuệ | Gợi ý loại sự cố và mức ưu tiên (scikit-learn) có giải thích; người dùng xác nhận trước khi gửi; luật từ khóa dự phòng |

**Tầng 3 – DX-Helpdesk.** Giao diện người dùng cuối viết bằng Nuxt 4.

**Hệ thống của khách hàng (bên ngoài DX-OS).** Snipe-IT giữ danh mục tài sản, vị trí
(cơ sở, tòa, phòng), người đang giữ thiết bị và nhãn trạng thái. DX-Lab chỉ đọc và cập
nhật qua REST API của Snipe-IT, không sửa mã và không đọc thẳng database của nó.

## 2. Vai trò và phân quyền

Có 4 realm role trong Keycloak. Không thêm role theo cơ sở; cơ sở là thuộc tính riêng
(mục 2.1).

**`ROLE_STUDENT` – Người dùng.** Sinh viên, giảng viên, cán bộ. Xem thiết bị của mình,
báo hỏng, theo dõi ticket của mình, xác nhận hoặc sửa gợi ý AI, đánh giá sau khi đóng.

**`ROLE_TECHNICIAN` – Kỹ thuật viên.** Xem hàng đợi của cơ sở mình và việc được giao,
tiếp nhận, xử lý, lập biên bản.

**`ROLE_LAB_MANAGER` – Quản lý CNTT cơ sở.** Xem ticket của cơ sở mình, từ chối yêu
cầu không hợp lệ, phân công kỹ thuật viên cùng cơ sở, nghiệm thu hoặc mở lại, xem
dashboard.

**`ROLE_ADMIN` – Quản trị hệ thống.** Quản lý tài khoản, vai trò và thuộc tính cơ sở
trong Keycloak, cấu hình kết nối tới Snipe-IT, xem dashboard và giám sát.

### 2.1. Cơ sở làm việc (`co_so`)

- Mỗi kỹ thuật viên và quản lý có user attribute `co_so` trong Keycloak (`CS1`, `CS2`,
  `CS3`). Attribute được ánh xạ thành claim `co_so` trong access token.
- Gateway và Data API dùng claim này để lọc hàng đợi; không tin giá trị cơ sở do giao
  diện gửi lên.
- Người dùng (`ROLE_STUDENT`) không cần `co_so`; cơ sở của ticket lấy từ vị trí của
  thiết bị.
- Đổi realm để thêm attribute và mapper là một Issue riêng của M2; tài liệu này chỉ mô
  tả thiết kế.

### Ma trận phân quyền

| Chức năng | STUDENT | TECHNICIAN | LAB_MANAGER | ADMIN |
|---|:-:|:-:|:-:|:-:|
| Xem thiết bị của mình | Có | Có | Có | Có |
| Báo hỏng, xem ticket của mình | Có | Có | Có | Có |
| Xem hàng đợi của cơ sở mình | | Có | Có | |
| Từ chối, phân công | | | Có (cơ sở mình) | |
| Tiếp nhận, cập nhật tiến độ, lập biên bản | | Có (việc được giao) | | |
| Nghiệm thu, đóng, mở lại | | | Có (cơ sở mình) | |
| Xem dashboard | | | Có (cơ sở mình) | Có (mọi cơ sở) |
| Quản trị hệ thống, cấu hình tích hợp | | | | Có |

## 3. Loại sự cố và mức ưu tiên

Ticket lưu trong PostgreSQL, kèm các trường provenance: `source`, `created_by`,
`created_at`, `updated_at`. `ticket_events` giữ nguồn của từng thay đổi, trạng thái
trước/sau, người thao tác và chi tiết. Giá trị `source` phân biệt `dx-helpdesk`
(người dùng thao tác), `snipe-it` (kết quả đồng bộ từ hệ thống tài sản), `nats`
(sự kiện từ trục tích hợp, dự kiến M3). Kết quả cập nhật tài sản thành công hay
thất bại nằm trong lịch sử ticket.

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
| `HIGH` | Hỏng máy chủ hoặc thiết bị mạng trung tâm, nhiều người bị ảnh hưởng |
| `MEDIUM` | Lỗi trên một máy, người dùng tạm chuyển sang máy khác được |
| `LOW` | Đề nghị cài thêm phần mềm, góp ý cải thiện |

## 4. Trạng thái ticket

Quy trình chạy trên Flowable, gọi qua gateway. Trạng thái ticket trong Data API phải
khớp với bước hiện tại của process instance.

| Trạng thái | Ý nghĩa | Trạng thái tài sản trên Snipe-IT |
|---|---|---|
| `DRAFT` | Người dùng đang soạn, chưa gửi | Không đổi |
| `SUBMITTED` | Đã gửi, đã gắn cơ sở theo vị trí thiết bị, nằm trong hàng đợi của quản lý cơ sở đó | Không đổi |
| `ASSIGNED` | Quản lý đã giao cho một kỹ thuật viên cùng cơ sở | Không đổi |
| `IN_PROGRESS` | Kỹ thuật viên đã nhận và đang xử lý | "Đang sửa chữa" |
| `RESOLVED` | Kỹ thuật viên xử lý xong, đã lập biên bản, chờ nghiệm thu | "Đang sửa chữa" |
| `CLOSED` | Quản lý nghiệm thu và đóng; số liệu được tính vào dashboard | Trả về nhãn trước khi sửa, thường là "Sẵn sàng" |
| `REJECTED` | Quản lý từ chối ở bước tiếp nhận, ghi lý do; quy trình kết thúc | Không đổi |

Tên nhãn trạng thái là ví dụ cấu hình trong Snipe-IT; ánh xạ thật cấu hình trong dịch
vụ tích hợp.

Chuyển trạng thái:

```
DRAFT -> SUBMITTED -> ASSIGNED -> IN_PROGRESS -> RESOLVED -> CLOSED
            |                         ^              |
            v                         +--- Mở lại ---+
         REJECTED
```

- **Từ chối** chỉ ở bước tiếp nhận: `SUBMITTED` sang `REJECTED`, bắt buộc có lý do, quy
  trình kết thúc luôn.
- **Mở lại** chỉ ở bước nghiệm thu: `RESOLVED` quay về `IN_PROGRESS` cho đúng kỹ thuật
  viên đã xử lý, bắt buộc có lý do. Bảng lịch sử ghi `action = 'REOPEN'`. Biên bản cũ
  vẫn nằm trong lịch sử. Không thêm trạng thái mới nên không đổi schema.

## 5. Kịch bản sử dụng

Chuỗi demo chính đi qua kịch bản 1 đến 4; kịch bản 5, 6, 7 là nhánh phụ.

### Kịch bản 1: Đăng nhập và xem thiết bị của tôi

- **Người thực hiện:** người dùng (`ROLE_STUDENT`).
- **Điều kiện:** tài khoản Keycloak trùng username với người dùng trên Snipe-IT.

1. Mở DX-Helpdesk, đăng nhập SSO qua Keycloak.
2. Mở "Thiết bị của tôi". Giao diện gọi `GET /api/assets/me` qua APISIX.
3. Dịch vụ tích hợp tài sản tìm người dùng trên Snipe-IT theo username, gọi
   `GET /api/v1/users/{id}/assets`, trả về danh sách thiết bị kèm vị trí và cơ sở.
4. Với máy trong phòng thực hành (không giao riêng cho ai), người dùng chọn cơ sở và
   phòng, hoặc nhập mã tài sản dán trên máy (`GET /api/v1/hardware/bytag/{tag}`).

**Kết quả:** người dùng thấy đúng thiết bị của mình, không phải gõ lại mã và vị trí.

### Kịch bản 2: Báo hỏng và định tuyến theo cơ sở

- **Người thực hiện:** người dùng (`ROLE_STUDENT`), dịch vụ AI.
- **Điều kiện:** đã chọn thiết bị ở kịch bản 1.

1. Chọn thiết bị, nhập mô tả ("Máy PC-04 phòng 301 không khởi động, có mùi khét"),
   đính kèm ảnh. Ảnh được tải lên SeaweedFS qua `/api/files`.
2. Giao diện gọi `POST /api/ai/classify`, hiện gợi ý loại và mức ưu tiên kèm từ khóa
   giải thích (kịch bản 6). Người dùng giữ hoặc sửa.
3. Bấm gửi. Data API lưu ticket kèm mã tài sản và cơ sở lấy từ vị trí thiết bị, rồi khởi
   tạo quy trình trên Flowable.
4. Định tuyến: cơ sở của ticket quyết định hàng đợi. M2 dùng bảng ánh xạ vị trí
   Snipe-IT sang cơ sở; M3 thay bằng truy vấn không gian PostGIS, dùng được cả khi
   thiết bị chưa có vị trí trong Snipe-IT nhưng người báo gửi kèm tọa độ.

**Kết quả:** ticket `SUBMITTED`, nằm trong hàng đợi của quản lý đúng cơ sở. Quản lý cơ
sở khác không thấy ticket này.

### Kịch bản 3: Phân công và xử lý

- **Người thực hiện:** quản lý cơ sở (`ROLE_LAB_MANAGER`), kỹ thuật viên
  (`ROLE_TECHNICIAN`).
- **Điều kiện:** ticket `SUBMITTED` thuộc cơ sở của quản lý.

1. Quản lý mở hàng đợi, xem ticket kèm thông tin thiết bị lấy từ Snipe-IT (model, ngày
   mua, lịch sử ticket trước đó của thiết bị), chốt mức ưu tiên, giao cho một kỹ thuật
   viên cùng cơ sở. Ticket sang `ASSIGNED`.
2. Kỹ thuật viên mở "Công việc của tôi", chọn "Tiếp nhận". Ticket sang `IN_PROGRESS`;
   tài sản trên Snipe-IT được đặt nhãn "Đang sửa chữa".
3. Kỹ thuật viên kiểm tra, sửa, nhập biên bản (nguyên nhân, linh kiện thay), bấm
   "Hoàn thành". Ticket sang `RESOLVED`.

**Kết quả:** ticket chờ nghiệm thu; người khác tra trên Snipe-IT thấy máy đang sửa.

### Kịch bản 4: Nghiệm thu và cập nhật hệ thống tài sản

- **Người thực hiện:** quản lý cơ sở (`ROLE_LAB_MANAGER`), người dùng.
- **Điều kiện:** ticket `RESOLVED`.

1. Quản lý kiểm tra biên bản, chọn "Nghiệm thu và đóng".
2. Quy trình trên Flowable kết thúc, ticket sang `CLOSED`.
3. Tài sản trên Snipe-IT trả về nhãn trước khi sửa và được ghi chú số ticket, nội dung
   biên bản. M2 cập nhật trực tiếp qua dịch vụ tích hợp; M3 đi qua sự kiện NATS (mục 6).
4. Người dùng nhận thông báo và đánh giá mức độ hài lòng. Số liệu được cộng vào
   `/api/data/stats`.

**Kết quả:** dashboard có số ticket theo cơ sở, thời gian xử lý so với SLA, tỷ lệ hài
lòng; Snipe-IT có lịch sử sửa chữa của thiết bị.

### Kịch bản 5: Từ chối ở bước tiếp nhận

- **Người thực hiện:** quản lý cơ sở (`ROLE_LAB_MANAGER`).
- **Điều kiện:** ticket `SUBMITTED`.

1. Quản lý thấy yêu cầu không hợp lệ, ví dụ xin cài phần mềm không được phép, hoặc báo
   trùng một ticket đang mở của cùng thiết bị.
2. Chọn "Từ chối" và ghi lý do.
3. Flowable đi theo nhánh từ chối, ticket sang `REJECTED`, quy trình kết thúc. Snipe-IT
   không bị thay đổi.

**Kết quả:** người tạo xem được ticket bị từ chối kèm lý do.

### Kịch bản 6: Gợi ý loại sự cố và mức ưu tiên

- **Người thực hiện:** người dùng (`ROLE_STUDENT`), dịch vụ AI.
- **Điều kiện:** dịch vụ AI chạy sau gateway (`/api/ai`).

1. Người dùng nhập mô tả: "Màn hình máy 12 bị chớp, có sọc tím, có mùi khét".
2. Giao diện gọi `POST /api/ai/classify` qua APISIX.
3. Mô hình phân loại (scikit-learn) đề xuất `HARDWARE`, `URGENT` và hiện các từ khóa dẫn
   tới kết quả.
4. Nếu mô hình không phản hồi, dịch vụ dùng bộ quy tắc từ khóa ("mùi khét", "chớp").
5. Người dùng xem gợi ý, giữ nguyên hoặc sửa, rồi mới gửi. Mức ưu tiên cuối cùng do quản
   lý chốt ở kịch bản 3.

**Kết quả:** ticket có sẵn loại và mức ưu tiên khi gửi; gợi ý không tự chuyển trạng thái
quy trình.

### Kịch bản 7: Mở lại khi nghiệm thu không đạt

- **Người thực hiện:** quản lý cơ sở (`ROLE_LAB_MANAGER`).
- **Điều kiện:** ticket `RESOLVED`.

1. Quản lý kiểm tra thấy lỗi chưa hết, chọn "Mở lại" và ghi lý do.
2. Flowable quay về bước xử lý, giao lại đúng kỹ thuật viên cũ. Ticket về `IN_PROGRESS`.
3. Lịch sử ghi `REOPEN` kèm lý do; tài sản trên Snipe-IT vẫn ở "Đang sửa chữa".

**Kết quả:** ticket xuất hiện lại trong "Công việc của tôi" của kỹ thuật viên; số lần mở
lại được tính vào dashboard.

<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Dữ liệu mẫu 3 cơ sở HaUI và nguồn dữ liệu mở (`data/samples/`)

Thư mục này chứa dữ liệu mẫu chuẩn hóa cho Đại học Công nghiệp Hà Nội (HaUI) với 3 cơ sở (`CS1`, `CS2`, `CS3`), phục vụ demo chuỗi tích hợp, định tuyến ticket, bảng điều khiển thống kê (dashboard) và huấn luyện mô hình AI phân loại sự cố (issue #23).

## 1. Cấu trúc các tệp dữ liệu

| Tệp | Định dạng | Mục đích sử dụng |
|---|---|---|
| `campuses.json` | JSON | Danh mục 3 cơ sở, địa chỉ, tòa nhà, phòng máy. Tọa độ và ranh giới là ước lượng, do đội tự xác định để minh họa |
| `snipeit_seed.json` | JSON | Dữ liệu nạp vào hệ thống quản lý tài sản Snipe-IT (cây vị trí, nhãn trạng thái, danh mục, model, tài khoản người dùng, tài sản) |
| `tickets_seed.sql` | SQL | Script nạp dữ liệu vào cơ sở dữ liệu PostgreSQL `dxdata` (bảng `tickets`, `ticket_attachments`, `ticket_events`) |
| `tickets.json` | JSON | Bản sao snapshot của các ticket mẫu phục vụ kiểm thử API độc lập và giao diện frontend offline |
| `training_data.jsonl` | JSON Lines | 160 mẫu sự cố CNTT tiếng Việt có gắn nhãn loại sự cố (`category`) và mức ưu tiên (`priority`) phục vụ huấn luyện mô hình scikit-learn (M3.22) |

---

## 2. Thông tin 3 cơ sở HaUI

Tọa độ và ranh giới là ước lượng, do đội tự xác định để minh họa.

1. **Cơ sở 1 – Trụ sở chính (Minh Khai)**
   - **Mã:** `CS1`
   - **Địa chỉ:** Số 298 đường Cầu Diễn, phường Minh Khai, quận Bắc Từ Liêm, TP. Hà Nội.
   - **Tọa độ:** 21.05372°N, 105.73511°E (ước lượng).
   - **Tòa nhà mẫu:** Tòa C (Trung tâm Đào tạo & TT CNTT), Tòa A10 (Giảng đường & Thực hành chuyên sâu), Tòa A1 (Điều hành).
   - **Phòng máy tiêu biểu:** Phòng Lab C301, Phòng Lab C302, Phòng Thực hành 401, 402, Phòng Mạng A10-502.

2. **Cơ sở 2 – Tây Tựu**
   - **Mã:** `CS2`
   - **Địa chỉ:** Phường Tây Tựu, quận Bắc Từ Liêm, TP. Hà Nội.
   - **Tọa độ:** 21.06644°N, 105.71958°E (ước lượng).
   - **Tòa nhà mẫu:** Tòa B1 (Giảng đường & Thực hành Tin học), Tòa B2 (Trung tâm Thí nghiệm Điện tử).
   - **Phòng máy tiêu biểu:** Phòng Thực hành 201, 202, Phòng Lab Đa phương tiện B2-301.

3. **Cơ sở 3 – Hà Nam**
   - **Mã:** `CS3`
   - **Địa chỉ:** Phường Lê Hồng Phong, thành phố Phủ Lý, tỉnh Hà Nam.
   - **Tọa độ:** 20.54862°N, 105.91888°E (ước lượng).
   - **Tòa nhà mẫu:** Tòa H1 (Khu thực hành Công nghệ cao), Tòa H2 (Giảng đường Đa năng).
   - **Phòng máy tiêu biểu:** Phòng Thực hành 301, 302, Phòng Lab Kỹ thuật Mạng H2-205.

---

## 3. Cấu trúc tài sản và người dùng (Khớp Snipe-IT và Keycloak)

- **Người dùng:** Trùng username với tài khoản demo trong Keycloak (`sinhvien`, `kythuatvien`, `truongphong`, `quantri`) và các tài khoản mở rộng cho cơ sở 2, 3 (`sinhvien_cs2`, `kythuatvien_cs2`, `truongphong_cs2`, `sinhvien_cs3`, `kythuatvien_cs3`, `truongphong_cs3`).
- **Nhãn trạng thái trên Snipe-IT:**
  - `Sẵn sàng` (Deployable): Thiết bị hoạt động bình thường, sẵn sàng cấp phát hoặc sử dụng.
  - `Đang sửa chữa` (Pending): Thiết bị có ticket báo hỏng đang được kỹ thuật viên xử lý.
  - `Đang bảo trì` (Maintenance): Thiết bị trong lịch bảo dưỡng.
  - `Thanh lý` (Archived): Thiết bị hỏng hoàn toàn.
- **Tài sản mẫu:**
  - Thiết bị giao cho cá nhân (phục vụ màn hình "Thiết bị của tôi" `GET /api/assets/me`): Laptop Dell Latitude 5420 của sinh viên (`HAUI-LT-0001`), máy trạm cố định (`HAUI-PC-0002`).
  - Thiết bị cố định theo phòng máy (cho phép tra cứu theo mã dán trên máy `asset_tag`): Máy trạm PC phòng máy CS1, CS2, CS3, switch mạng Cisco Catalyst 2960-X, máy chiếu Panasonic.
  - Các tài sản `HAUI-CS1-PC02` và `HAUI-CS2-PC02` ở trạng thái "Đang sửa chữa", tương ứng với các ticket đang ở trạng thái `IN_PROGRESS` bên `dxdata`.

---

## 4. Dữ liệu ticket và các nhánh quy trình BPMN

Dữ liệu trong `tickets_seed.sql` và `tickets.json` bao phủ 100% các trạng thái và nghiệp vụ trong `docs/usecases.md`:
1. `DRAFT`: Bản nháp chưa gửi của sinh viên (`a1111111-06`).
2. `SUBMITTED`: Ticket đã nộp, định tuyến vào hàng đợi trưởng phòng lab tương ứng tại CS1, CS2, CS3 (`a1111111-05`, `b2222222-02`, `c3333333-02`).
3. `ASSIGNED`: Quản lý đã phân công cho kỹ thuật viên cùng cơ sở (`a1111111-04`).
4. `IN_PROGRESS`: Kỹ thuật viên đang xử lý, trạng thái thiết bị bên Snipe-IT chuyển thành "Đang sửa chữa" (`a1111111-02`, `b2222222-01`).
5. `RESOLVED`: Kỹ thuật viên xử lý xong và lập biên bản giải quyết `resolution_summary`, chờ nghiệm thu (`a1111111-03`).
6. `CLOSED`: Quản lý nghiệm thu và đóng ticket, đánh giá sao hài lòng (`satisfaction_rating` từ 4 đến 5 sao), thiết bị Snipe-IT trở lại "Sẵn sàng" (`a1111111-01`, `c3333333-01`).
7. `REJECTED`: Quản lý từ chối tại bước tiếp nhận có ghi rõ `rejection_reason` bắt buộc (`b2222222-03`).
8. **Nhánh Mở lại (REOPEN):** Ticket `e1111111-12` ghi nhận lịch sử đầy đủ trong `ticket_events` với sự kiện `REOPEN` từ `RESOLVED` quay lại `IN_PROGRESS` kèm lý do, trước khi được kỹ thuật viên hoàn thiện và đóng ticket thành công.

---

## 5. Dữ liệu huấn luyện AI phân loại sự cố (M3.22)

Tệp `training_data.jsonl` gồm 160 mẫu tình huống sự cố thực tế bằng tiếng Việt, được phân bố cân bằng 40 mẫu cho mỗi loại sự cố (`category`):
- `HARDWARE` (40 mẫu): Hỏng nguồn, sập màn hình, lỗi card đồ họa, hỏng phím chuột, máy chiếu, bad sector ổ cứng...
- `SOFTWARE_ENVIRONMENT` (40 mẫu): Lỗi Windows Update, Docker Desktop WSL2, Visual Studio SDK, thư viện PyTorch, bản quyền MATLAB, xung đột biến môi trường...
- `NETWORK_ACCOUNT` (40 mẫu): Mất mạng LAN, đứt cáp quang, lỗi DHCP/DNS, mất sóng WiFi, quên mật khẩu SSO, lỗi mở port firewall...
- `LAB_ASSET` (40 mẫu): Hỏng điều hòa phòng máy, vỡ ống nước, mượn phòng học ngoài giờ, kiểm kê tài sản, bàn ghế gãy hỏng, bình cứu hỏa tụt áp...

Các mẫu được gán mức ưu tiên tương ứng (`URGENT`, `HIGH`, `MEDIUM`, `LOW`) theo tiêu chí ảnh hưởng tới hoạt động thi cử, giảng dạy và học tập.

---

## 6. Hướng dẫn nạp dữ liệu (`make seed`)

Chạy lệnh nạp dữ liệu từ thư mục gốc của repository:

```bash
# Nạp toàn bộ dữ liệu mẫu vào cả PostgreSQL và Snipe-IT (nếu service đang chạy)
make seed

# Hoặc chạy script trực tiếp qua Python với các tùy chọn
py scripts/seed.py --help
py scripts/seed.py --dry-run    # Kiểm tra tính hợp lệ của toàn bộ dữ liệu mẫu
py scripts/seed.py --db-only    # Chỉ nạp vào cơ sở dữ liệu dxdata
py scripts/seed.py --snipeit    # Chỉ đồng bộ cấu hình sang Snipe-IT qua REST API
```

---

## 7. Cam kết dữ liệu mở và bảo vệ quyền riêng tư

- **Không chứa dữ liệu cá nhân thật (PII):** Toàn bộ họ tên, mã sinh viên, email, số điện thoại, số sê-ri thiết bị trong bộ dữ liệu này là **dữ liệu giả lập (synthetic data)** do đội phát triển DX-Lab tạo lập.
- **Giấy phép & Nguồn dữ liệu:**
  - Tọa độ và ranh giới 3 cơ sở là ước lượng, do đội tự xác định để minh họa.
  - Toàn bộ dữ liệu mẫu ticket, tài sản và cấu hình thuộc dự án DX-Lab, phát hành theo giấy phép **Apache-2.0**.

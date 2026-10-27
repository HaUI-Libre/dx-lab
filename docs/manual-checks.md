<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Kiểm tra bằng tay

Tài liệu này hướng dẫn các bước kiểm tra thủ công giao diện và luồng nghiệp vụ thực tế
trên trình duyệt – những phần kiểm thử tự động chưa bao quát trọn vẹn vì cần tương tác
trực quan và xác nhận bằng mắt người.

## 0. Chuẩn bị môi trường

1. Dựng và khởi động đầy đủ các dịch vụ:
   ```bash
   make env
   make demo
   make seed
   ```
2. Mật khẩu cho các tài khoản demo được quy định tại biến `DEMO_USER_PASSWORD` trong `.env`
   (mặc định là `dxlab@2026` trong `.env.example`).
3. Khi `DEMO_LOGIN_HINTS=true` (mặc định), màn hình đăng nhập cung cấp sẵn các nút
   **"Vào thử theo vai trò"** (`sinhvien`, `truongphong`, `kythuatvien`, `quantri`). Bấm
   vào nút sẽ tự động chuyển sang trang Keycloak và điền sẵn tên đăng nhập, bạn chỉ cần
   nhập mật khẩu demo mà không cần mở nhiều cửa sổ ẩn danh riêng biệt.
4. **Lưu ý quan trọng:**
   - **Phiếu mẫu từ `make seed`:** Các phiếu mẫu có sẵn trong cơ sở dữ liệu không gắn với
     tiến trình Flowable đang chạy, nên khi bấm thao tác chuyển bước quy trình sẽ trả về
     lỗi `409 Conflict`. Luôn tạo một phiếu mới để kiểm tra trọn vẹn luồng nghiệp vụ.
   - **Trang thống kê (`/dashboard`):** Trang thống kê hiển thị khung giao diện nhưng
     chưa có số liệu tổng hợp động nếu tính năng API thống kê (#22) chưa hoàn thành.

---

## 1. Đi một vòng quy trình nghiệp vụ chính

### Bước 1: Đăng nhập bằng nút vào thử và kiểm tra kết nối thời gian thực
- **Thao tác:** Mở trình duyệt truy cập `http://localhost:3000`. Tại mục **Vào thử theo vai trò**,
  bấm chọn thẻ **Sinh viên** (`sinhvien`). Tại trang xác thực Keycloak, tên đăng nhập đã được
  điền sẵn, nhập mật khẩu demo và bấm **Log In**.
- **Kết quả mong đợi:** Đăng nhập thành công và quay lại trang chủ DX-Helpdesk. Trên thanh
  header xuất hiện chấm xanh kèm chữ **Trực tiếp** (biểu thị kết nối Server-Sent Events sẵn sàng).
  Trang chủ hiển thị lời chào cùng định danh `sinhvien`.

### Bước 2: Báo hỏng thiết bị kèm ảnh đính kèm
- **Thao tác:** Bấm nút **Báo hỏng** trên trang chủ (hoặc bấm `Ctrl+K` gõ chọn "Báo hỏng thiết bị"):
  1. Khối *Thiết bị*: Hiển thị danh sách thiết bị mượn của sinh viên lấy từ Snipe-IT (ví dụ `HAUI-LT-0001` tại Cơ sở 1). Chọn thiết bị này, trường cơ sở và vị trí tự động được điền.
  2. Khối *Thông tin sự cố*: Nhập tiêu đề (ví dụ: `Màn hình laptop không lên nguồn`) và mô tả sự cố.
  3. Khối *Gợi ý phân loại (AI)*: Hệ thống phân loại hiển thị gợi ý danh mục và mức ưu tiên. Bấm nút **Dùng gợi ý** để tự động cập nhật mức ưu tiên tương ứng.
  4. Khối *Tệp đính kèm*: Chọn một ảnh chụp thực tế (.png hoặc .jpg).
  5. Bấm **Gửi yêu cầu**.
- **Kết quả mong đợi:** Hiển thị màn hình thông báo gửi thành công kèm mã phiếu dạng `DXL-NNNN`.
  Bấm xem chi tiết phiếu: trạng thái là `Chờ tiếp nhận`, hiển thị ảnh đã tải lên từ SeaweedFS
  và dòng sự kiện khởi tạo trong lịch sử xử lý.

### Bước 3: Hàng đợi theo cơ sở và phân công kỹ thuật viên
- **Thao tác:** Đăng xuất và dùng nút vào thử để đăng nhập tài khoản **Trưởng phòng lab** (`truongphong` - Cơ sở 1).
  Vào mục **Yêu cầu**:
  1. Danh sách tự động hiển thị hàng đợi của Cơ sở 1 (`Hàng đợi CS1`). Phiếu vừa tạo ở Bước 2 nằm ngay đầu danh sách.
  2. Bấm vào phiếu để mở trang chi tiết, bấm nút **Tiếp nhận**.
  3. Sau khi tiếp nhận, bấm nút **Phân công**. Hộp thoại danh sách kỹ thuật viên chỉ liệt kê các nhân sự thuộc CS1. Chọn `kythuatvien` và xác nhận phân công.
- **Kết quả mong đợi:** Phiếu chuyển sang trạng thái `Đã phân công`. Lịch sử ghi nhận sự kiện phân công cho `kythuatvien`.

### Bước 4: Kỹ thuật viên nhận việc và cập nhật tài sản tự động
- **Thao tác:** Đăng nhập tài khoản **Kỹ thuật viên** (`kythuatvien`). Vào **Yêu cầu**:
  1. Phiếu được phân công hiển thị trong danh sách "Việc của tôi". Bấm mở chi tiết phiếu.
  2. Bấm nút **Nhận việc**.
  3. Mở tab mới truy cập hệ thống Snipe-IT (`http://127.0.0.1:8081`): Tài sản `HAUI-LT-0001` đã được đồng bộ tự động chuyển sang nhãn trạng thái "Đang sửa chữa".
- **Kết quả mong đợi:** Phiếu chuyển sang trạng thái `Đang xử lý`. Giao diện chi tiết phiếu của kỹ thuật viên xuất hiện ô nhập "Biên bản xử lý".

### Bước 5: Chế độ xem cột và kéo thả (Board Kanban)
- **Thao tác:** Tại trang danh sách **Yêu cầu**, ở góc trên danh sách chọn chế độ xem **Cột**
  (hoặc thêm tham số `?xem=cot` trên URL):
  1. *Thử kéo thả không hợp lệ:* Thử kéo thẻ phiếu từ cột `Đang xử lý` thả vào cột `Chờ tiếp nhận` hoặc `Đã đóng`.
     - **Kết quả mong đợi:** Thẻ phiếu tự động trượt về vị trí cũ (snap back) kèm thông báo từ chối thao tác không hợp lệ.
  2. *Kéo thả hợp lệ sang bước kế tiếp:* Kéo thẻ phiếu từ cột `Đang xử lý` thả vào cột `Chờ nghiệm thu`.
     - **Kết quả mong đợi:** Hộp thoại yêu cầu nhập biên bản xử lý bật lên. Nhập nội dung biên bản (ví dụ: `Đã thay cáp màn hình và vệ sinh máy`) rồi bấm xác nhận. Thẻ phiếu chuyển thành công sang cột `Chờ nghiệm thu`.

### Bước 6: Nghiệm thu và nhánh mở lại
- **Thao tác:** Đăng nhập lại tài khoản `truongphong`, mở chi tiết phiếu đang ở trạng thái `Chờ nghiệm thu`:
  1. *Thử mở lại thiếu lý do:* Bấm nút **Mở lại** khi chưa nhập lý do.
     - **Kết quả mong đợi:** Hệ thống chặn lại với thông báo "Cần nhập lý do mở lại".
  2. *Mở lại có lý do:* Nhập lý do (ví dụ: `Kiểm tra lại màn hình vẫn bị chớp`) rồi bấm **Mở lại**.
     - **Kết quả mong đợi:** Phiếu chuyển về trạng thái `Đang xử lý`, tự động giao lại cho kỹ thuật viên cũ (`kythuatvien`). Tiến trình ghi nhận số lần mở lại.
  3. Kỹ thuật viên `kythuatvien` mở phiếu, nhập biên bản lần hai (ví dụ: `Đã thay thế linh kiện màn hình mới hoàn toàn`) và bấm **Đánh dấu hoàn thành** -> Phiếu sang `Chờ nghiệm thu`.
  4. Trưởng phòng `truongphong` kiểm tra biên bản mới và bấm **Nghiệm thu và đóng**.
- **Kết quả mong đợi:** Phiếu chuyển sang trạng thái `Đã đóng`. Hệ thống Snipe-IT tự động cập nhật trả lại nhãn trạng thái ban đầu cho thiết bị kèm ghi chú mã phiếu xử lý.

### Bước 7: Trạng thái cập nhật trực tiếp và đánh giá chất lượng
- **Thao tác:**
  1. Mở song song 2 cửa sổ trình duyệt: một bên là tài khoản `sinhvien` đang mở trang chi tiết phiếu, một bên là tài khoản `truongphong`.
  2. Khi trưởng phòng bấm nghiệm thu đóng phiếu, quan sát cửa sổ của sinh viên.
     - **Kết quả mong đợi:** Tab của sinh viên tự động cập nhật sang trạng thái `Đã đóng` theo thời gian thực (nhờ sự kiện SSE) mà không cần bấm F5 tải lại trang.
  3. Trên giao diện sinh viên, tại khối "Đánh giá chất lượng phục vụ": bấm chọn 5 sao, nhập nhận xét và bấm **Gửi đánh giá**.
     - **Kết quả mong đợi:** Thông báo ghi nhận đánh giá thành công.

---

## 2. Nhánh từ chối yêu cầu

- **Thao tác:**
  1. Sinh viên `sinhvien` tạo một phiếu báo hỏng mới.
  2. Trưởng phòng `truongphong` vào hàng đợi mở phiếu ở trạng thái `Chờ tiếp nhận`, bấm **Từ chối**.
  3. Bấm xác nhận từ chối khi chưa nhập lý do -> Bị chặn: yêu cầu bắt buộc có lý do từ chối.
  4. Nhập lý do (ví dụ: `Thiết bị thuộc phòng lab chuyên đề khác, vui lòng liên hệ CS2`) và bấm xác nhận.
- **Kết quả mong đợi:** Phiếu chuyển sang trạng thái `Bị từ chối`, tiến trình kết thúc. Sinh viên mở phiếu thấy rõ lý do bị từ chối trong khung cảnh báo và trong lịch sử.

---

## 3. Bảng lệnh nhanh (Command Palette Ctrl+K) và Tra cứu phiếu

- **Bảng lệnh `Ctrl+K`:**
  - Bấm tổ hợp phím `Ctrl+K` (hoặc `Cmd+K` trên macOS, hoặc bấm nút **Ctrl K** trên thanh tìm kiếm header).
  - Bảng lệnh mở ra ở giữa màn hình: cho phép chuyển nhanh tới Báo hỏng, Danh sách phiếu, Cổng thông tin [H], hoặc chuyển đổi giao diện Sáng / Tối.
- **Tìm kiếm theo mã phiếu:**
  - Nhập mã phiếu dạng `DXL-NNNN` hoặc dán trực tiếp mã UUID của phiếu vào ô tìm kiếm trên header rồi nhấn Enter.
  - **Kết quả mong đợi:** Hệ thống chuyển hướng thẳng đến trang chi tiết của phiếu cần tìm.

---

## 4. Dự phòng khi hệ thống phụ trợ gián đoạn

### 4.1. Dịch vụ AI phân loại không sẵn sàng
- **Thao tác:** Tạm dừng service AI: `docker compose stop ai`. Quay lại form báo hỏng và nhập mô tả sự cố.
- **Kết quả mong đợi:** Khối phân loại tự động chuyển sang luật dự phòng dựa trên từ khóa (rule-based fallback), hoặc hiển thị thông báo "Chưa có gợi ý". Người dùng vẫn chủ động chọn danh mục, mức ưu tiên và gửi phiếu thành công mà không bị nghẽn quy trình. Khởi động lại service: `docker compose start ai`.

### 4.2. Hệ thống tài sản Snipe-IT không sẵn sàng
- **Thao tác:** Tạm dừng service tích hợp tài sản: `docker compose stop asset-sync`. Vào form báo hỏng.
- **Kết quả mong đợi:** Form hiển thị thông báo "Chưa kết nối được hệ thống tài sản...". Sinh viên vẫn có thể tự chọn vị trí phòng lab từ danh mục có sẵn và gửi yêu cầu bình thường. Khởi động lại service: `docker compose start asset-sync`.

---

## 5. Bảng điều khiển vận hành Grafana

- **Thao tác:** Mở trình duyệt truy cập `http://127.0.0.1:3001`, đăng nhập bằng tài khoản `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD` (từ file `.env`).
- **Kết quả mong đợi:** Dashboard "DX-Lab: tổng quan vận hành" hiển thị đầy đủ biểu đồ giám sát gateway APISIX, số lượng ticket theo trạng thái, hoạt động luồng quy trình BPMN, hàng đợi NATS và kết nối PostgreSQL có số liệu phát sinh sau chuỗi thao tác ở Mục 1.

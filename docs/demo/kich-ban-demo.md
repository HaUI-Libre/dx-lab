<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Kịch bản demo 10 phút (#42, bản nháp)

Bản nháp để đội duyệt. Người nói, thời lượng và tài khoản có thể đổi; phần ghi
"chờ" là tính năng chưa xong lúc soạn, chỉ đưa vào nếu đã chạy trước buổi tổng duyệt.

## Chuẩn bị trước buổi (30 phút trước)

- Máy demo đã `make env`, `make demo`, `make seed`; `make smoke`, `make smoke-assets`
  đạt. Không chạy `docker compose down -v` sau bước này.
- Mở sẵn 4 cửa sổ ẩn danh: `sinhvien`, `truongphong`, `kythuatvien`, `quantri`; một
  tab Snipe-IT (http://127.0.0.1:8081) ở trang thiết bị `HAUI-LT-0001`; một tab Grafana
  (http://127.0.0.1:3001).
- Chuẩn bị một ảnh lỗi màn hình (PNG) trên máy.
- Video dự phòng (#43) mở sẵn, phòng khi mạng hoặc máy gặp sự cố.

## Diễn biến

| Phút | Người nói | Nội dung | Màn hình |
|---|---|---|---|
| 0:00–1:00 | Trung | Bài toán: trường có 3 cơ sở, phần mềm quản lý tài sản có sẵn; báo hỏng thiết bị đang qua điện thoại, giấy. DX-Lab dựng một DX-OS Open-Core rồi chạy DX-Helpdesk trên đó, nối với hệ thống tài sản có sẵn chứ không thay nó | Slide 1–2 |
| 1:00–2:30 | Trung | Kiến trúc 3 tầng, H-P-D-I, 7 lớp của đề ánh xạ vào thành phần nào; mọi lời gọi qua APISIX với token Keycloak; toàn bộ là phần mềm OSI, dựng bằng `make up` | Slide 3–5 |
| 2:30–3:30 | Linh | Đăng nhập SSO bằng `sinhvien`; "Thiết bị của tôi" lấy từ Snipe-IT; báo hỏng `HAUI-LT-0001` kèm ảnh | App, cửa sổ `sinhvien` |
| 3:30–4:30 | Nam Anh | Ticket tự định tuyến về CS1 theo vị trí thiết bị đã xác minh trên Snipe-IT, không tin cơ sở do giao diện gửi; `truongphong` CS1 tiếp nhận, phân công: danh sách chỉ có kỹ thuật viên CS1; trưởng phòng CS2 không thấy ticket | App, cửa sổ `truongphong` |
| 4:30–5:30 | Nam Anh | `kythuatvien` nhận việc; chuyển sang tab Snipe-IT: nhãn thiết bị đã thành "Đang sửa chữa" (sự kiện qua NATS); nhập biên bản, hoàn thành | App, Snipe-IT |
| 5:30–6:30 | Nam Anh | `truongphong` mở lại khi chưa nhập lý do bị chặn; nhập lý do rồi mở lại, kỹ thuật viên cũ nhận lại; hoàn thành, nghiệm thu và đóng; Snipe-IT trả nhãn cũ, ghi chú có số ticket | App, Snipe-IT |
| 6:30–7:15 | Linh | `sinhvien` xem lịch sử, provenance, đánh giá; nhánh từ chối có lý do | App |
| 7:15–8:00 | Trung | Grafana: request qua gateway, bước quy trình theo cơ sở, cập nhật tài sản; trang thống kê cho trưởng phòng (chờ #22) | Grafana, app |
| 8:00–8:45 | Nam Anh | Gợi ý phân loại trên form báo hỏng: gõ "màn hình chớp, có mùi khét", gợi ý kèm từ khoá; người dùng tự chấp nhận (chờ #31) | App |
| 8:45–10:00 | Trung | Tính mở và giấy phép: Apache-2.0, NOTICE, REUSE 121/121 tệp, gitleaks, CI dựng stack từ máy sạch và 5 check bắt buộc; Snipe-IT, Grafana AGPL chỉ chạy như dịch vụ riêng; vì sao thay Vault, MongoDB, n8n, Redpanda, ImmuDB | Slide 10–12 |

## Nếu có sự cố

| Sự cố | Cách xử lý |
|---|---|
| Snipe-IT chậm hoặc không lên | Tiếp tục bằng nhánh dự phòng: form ghi "Chưa kết nối được hệ thống tài sản", chọn vị trí tay; nói rõ đây là thiết kế (ADR-06) |
| Gợi ý phân loại không phản hồi | Form ghi "Chưa có gợi ý" và vẫn gửi; đúng ADR-05, AI không chặn quy trình |
| Mất phiên đăng nhập | Đăng nhập lại; tài khoản và mật khẩu ghi trên giấy |
| Máy demo hỏng | Chiếu video #43 |

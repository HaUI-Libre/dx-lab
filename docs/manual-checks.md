<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Kiểm tra bằng tay

Những việc test tự động chưa làm được vì cần trình duyệt thật hoặc mắt người. Chạy
trên máy sạch: `make env`, `make demo`, `make seed`. Mật khẩu tài khoản demo là
`DEMO_USER_PASSWORD` trong `.env`. Nên dùng cửa sổ ẩn danh cho mỗi vai trò để không
lẫn phiên đăng nhập.

## 1. Đi một vòng quy trình bằng trình duyệt (#26)

1. http://localhost:3000, đăng nhập `sinhvien`. Vào **Báo hỏng**:
   - Khối "Thiết bị" hiện thiết bị của sinhvien lấy từ Snipe-IT (ví dụ `HAUI-LT-0001`); chọn một thiết bị, vị trí tự điền.
   - Nhập tiêu đề, mô tả, chọn một ảnh PNG/JPEG, bấm **Gửi yêu cầu**.
   - Trang chi tiết hiện ảnh vừa tải và trạng thái "Chờ tiếp nhận".
2. Đăng nhập `truongphong` (CS1). Vào **Yêu cầu** thấy ticket ở hàng đợi CS1. Mở ticket: **Tiếp nhận**, rồi **Phân công** (danh sách chỉ có kỹ thuật viên CS1).
3. Đăng nhập `kythuatvien`: **Nhận việc**. Mở http://127.0.0.1:8081 (Snipe-IT): thiết bị chuyển nhãn "Đang sửa chữa". Quay lại app, nhập biên bản, **Đánh dấu hoàn thành**.
4. `truongphong`: bấm **Mở lại** khi chưa nhập lý do thì bị chặn; nhập lý do rồi mở lại. `kythuatvien` hoàn thành lần hai. `truongphong` **Nghiệm thu và đóng**. Snipe-IT trả nhãn cũ, ghi chú tài sản có số ticket.
5. `sinhvien`: lịch sử ticket có đủ các bước, có "Mở lại" kèm lý do; gửi đánh giá.
6. Nhánh từ chối: `sinhvien` gửi một yêu cầu khác; `truongphong` **Từ chối** có lý do; sinhvien thấy lý do.
7. Khi profile `integration` tắt (`make down && make up`): form báo hỏng ghi "Chưa kết nối được hệ thống tài sản", chọn vị trí bằng tay và vẫn gửi được.

## 2. Gợi ý phân loại (#32)

Cần dịch vụ phân loại (#31). Trên form báo hỏng, gõ mô tả như "Màn hình máy 12 bị chớp,
có sọc tím, có mùi khét": khối "Gợi ý phân loại" hiện loại, mức ưu tiên, từ khoá và
nguồn. Loại và mức chỉ đổi khi bấm **Dùng gợi ý**; vẫn sửa được trước khi gửi. Dừng
service `ai`: form ghi "Chưa có gợi ý" và vẫn gửi được.

## 3. Thống kê (#27)

Cần API thống kê (#22). Đăng nhập `truongphong`: menu có **Thống kê**, trang hiện số
liệu CS1. Đăng nhập `quantri`: chọn từng cơ sở và "Cả ba cơ sở". `sinhvien` không thấy
menu; mở thẳng `/dashboard` thì thấy thông báo không có quyền.

## 4. Grafana (#78)

http://127.0.0.1:3001, tài khoản `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD`.
Trang chủ là "DX-Lab: tổng quan vận hành". Sau khi đi vòng ở mục 1, các ô gateway, bước
quy trình theo cơ sở, cập nhật tài sản và PostgreSQL có số liệu.

## 5. Build trên máy sạch (#38)

Trên một máy chưa từng chạy dự án (Linux, hoặc Windows qua WSL2 theo README): clone,
`make env`, `make up`, `make smoke` đạt; thêm `make demo`, `make smoke-assets`,
`make smoke-monitoring`, `make test-e2e`. Thao tác gọi từ thư mục ngoài qua `make -C`.
Biên bản tại [docs/demo/bien-ban-build-may-sach.md](demo/bien-ban-build-may-sach.md):
Linux sạch đã có số liệu từ CI; Windows sạch qua WSL2 còn phải chạy, ghi bằng `time make ...`
và đính kèm output.

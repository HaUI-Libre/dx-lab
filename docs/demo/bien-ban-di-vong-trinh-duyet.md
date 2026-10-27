<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Biên bản đi một vòng nghiệp vụ bằng trình duyệt (M2.20)

- **Issue:** [#26](https://github.com/HaUI-Libre/dx-lab/issues/26), trang thống kê [#27](https://github.com/HaUI-Libre/dx-lab/issues/27)
- **Ngày chạy:** 26/10/2026, 08:45 đến 09:05
- **Cách chạy:** Google Chrome có giao diện (không headless) trên Windows 11; bấm,
  gõ, chọn tệp qua giao diện như người dùng. Mỗi vai trò đăng nhập qua đường dẫn của nút
  "Vào thử" (`/auth/login?hint=<tên>`) rồi nhập mật khẩu trên trang Keycloak; mật khẩu là
  `DEMO_USER_PASSWORD` mặc định của `.env.example`.
- **Stack:** `make demo` trên WSL2 (Kali), mọi profile, có dữ liệu mẫu của `make seed`.
  Data API chạy bản có `GET /stats` của [#156](https://github.com/HaUI-Libre/dx-lab/pull/156).

## 1. Vòng chính, có một lần mở lại

Phiếu `9F51913D`.

| Bước | Vai trò | Thao tác | Kết quả |
|---|---|---|---|
| 1 | `sinhvien` | Mở **Báo hỏng** | Khối "Thiết bị" hiện `HAUI-LT-0001`, `HAUI-PC-0002` lấy từ Snipe-IT |
| 2 | `sinhvien` | Chọn `HAUI-LT-0001`, nhập tiêu đề và mô tả | Gợi ý phân loại hiện "Phần cứng · Cao (theo mô hình)" kèm từ khoá; mức ưu tiên trên form vẫn "Trung bình" cho tới khi bấm **Dùng gợi ý** |
| 3 | `sinhvien` | Chọn một ảnh PNG, **Gửi yêu cầu** | Màn hình xác nhận có mã phiếu; trang chi tiết: "Chờ tiếp nhận", cơ sở CS1, mã tài sản 1, ưu tiên Cao, ảnh hiện trong phiếu và trong lịch sử |
| 4 | `truongphong` | Mở **Yêu cầu** | Hàng đợi CS1, phiếu mới ở đầu danh sách |
| 5 | `truongphong` | **Tiếp nhận**, rồi **Phân công** | Danh sách kỹ thuật viên chỉ có `kythuatvien` (CS1); phiếu sang "Đã phân công" |
| 6 | `kythuatvien` | **Nhận việc** | Phiếu sang "Đang xử lý"; lịch sử ghi sự kiện đã vào hàng đợi NATS; `asset-sync` ghi `SUCCEEDED`, lưu nhãn cũ của tài sản 1 |
| 7 | `kythuatvien` | **Đánh dấu hoàn thành** khi chưa có biên bản | Bị chặn: "Cần nhập biên bản xử lý." |
| 8 | `kythuatvien` | Nhập biên bản, hoàn thành | Phiếu sang "Chờ nghiệm thu" |
| 9 | `truongphong` | **Mở lại** khi chưa có lý do | Bị chặn: "Cần nhập lý do mở lại." |
| 10 | `truongphong` | Nhập lý do, mở lại | Phiếu về "Đang xử lý", vẫn giao `kythuatvien`; thanh tiến trình ghi "Mở lại 1 lần" |
| 11 | `kythuatvien` | Nhập biên bản lần hai, hoàn thành | "Chờ nghiệm thu" |
| 12 | `truongphong` | **Nghiệm thu và đóng** | "Đã đóng"; `asset-sync` trả nhãn cũ cho tài sản 1 (`CLOSED`, `SUCCEEDED`) |
| 13 | `sinhvien` | Mở phiếu | Lịch sử 14 dòng, có "Mở lại" kèm lý do và hai biên bản; trang hiện biên bản cuối |
| 14 | `sinhvien` | Chọn 4/5, **Gửi đánh giá** | "Đã gửi đánh giá. Cảm ơn bạn đã phản hồi." |

## 2. Nhánh từ chối

Phiếu `7440DB2D`, `sinhvien` xin cài trò chơi lên `HAUI-PC-0002`.

| Bước | Vai trò | Thao tác | Kết quả |
|---|---|---|---|
| 1 | `truongphong` | **Từ chối** khi chưa có lý do | Bị chặn: "Cần nhập lý do từ chối." |
| 2 | `truongphong` | Nhập lý do, từ chối | "Bị từ chối" |
| 3 | `sinhvien` | Mở phiếu | Thấy mục "Lý do từ chối" và dòng lịch sử kèm lý do; không còn thao tác nào |

## 3. Hệ thống tài sản không sẵn sàng

`docker stop` service `asset-sync` (tương đương tắt profile `integration` với trang
báo hỏng), rồi bật lại sau bước 3.

| Bước | Vai trò | Thao tác | Kết quả |
|---|---|---|---|
| 1 | `sinhvien` | Mở **Báo hỏng** | "Chưa kết nối được hệ thống tài sản, nên chưa lấy được thiết bị của bạn. Bạn vẫn báo hỏng được…" |
| 2 | `sinhvien` | Chọn vị trí `CS2-B1-PM201`, nhập tiêu đề, mô tả, gửi | Phiếu `B7A62452` "Chờ tiếp nhận", cơ sở CS2 theo vị trí, mã tài sản "Không có, báo theo vị trí" |

## 4. Trang thống kê

| Vai trò | Kết quả |
|---|---|
| `quantri` | "Thống kê toàn trường"; chọn Cơ sở 2 thì số liệu chỉ còn CS2 (3 phiếu) |
| `truongphong` | Menu có **Thống kê**; trang "Thống kê Cơ sở 1", biểu đồ theo cơ sở chỉ có CS1; tổng tăng đúng 2 phiếu CS1 tạo trong buổi kiểm tra |
| `sinhvien` | Menu không có **Thống kê**; mở thẳng `/dashboard` thì thấy "Không có quyền xem" |

## 5. Ghi nhận

- Lịch sử phiếu hiện người thực hiện bằng 8 ký tự đầu của `sub` (ví dụ `d8608553…`)
  khi người đó không phải người đang xem. Data API chỉ lưu `actor_sub`; muốn hiện tên
  cần thêm tra cứu người dùng, chưa làm.
- Sự kiện `ASSET_STATUS_UPDATE_QUEUED` hiện mã thô trong lịch sử vì thiếu nhãn tiếng
  Việt; sửa trong cùng PR với biên bản này.
- Kết quả cập nhật Snipe-IT qua NATS được `asset-sync` lưu ở kho riêng, lịch sử phiếu
  chỉ ghi "đã vào hàng đợi". Biên bản đọc kết quả trong kho của `asset-sync`; nhãn trên
  giao diện Snipe-IT không kiểm tra lại vì cần tài khoản quản trị Snipe-IT. `make
  smoke-assets` kiểm tra nhãn qua API.
- Trang thống kê chỉ nạp số liệu khi mở trang hoặc bấm **Làm mới**; tự cập nhật khi có
  phiếu mới làm ở #27.

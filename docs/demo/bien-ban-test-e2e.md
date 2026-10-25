<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Biên bản kiểm thử end-to-end theo chuỗi demo tích hợp (M3.28)

- **Issue:** [#34](https://github.com/HaUI-Libre/dx-lab/issues/34)
- **Lệnh:** `make test-e2e` (chạy `scripts/test-demo-e2e.py`), sau `make demo`
- **Ngày chạy:** 25/10/2026, 2 lần liên tiếp trên cùng một stack đang chạy

## 1. Môi trường đã chạy

| Mục | Giá trị |
|---|---|
| Máy | Windows 11 Pro (build 26200), WSL 3.0.3.0 |
| Linux trong WSL2 | Kali GNU/Linux Rolling, kernel 6.18.54.1-microsoft-standard-WSL2 |
| CPU, bộ nhớ cấp cho WSL | Intel Core i7-9750H, 12 luồng; 15 GB |
| Docker | Docker Engine 28.5.2 (gói Debian), Compose 2.40.3; không dùng Docker Desktop |
| Python chạy script | 3.14.7 |
| Stack | Mọi profile (`make demo`: lõi, `integration`, `monitoring`), image đã build sẵn, đã chạy khoảng một ngày |

## 2. Kết quả

| Lần | Đạt | Bỏ qua | Lỗi | Thời gian script |
|---|---|---|---|---|
| 1 | 31 | 2 | 0 | 12,3 giây |
| 2 | 31 | 2 | 0 | 10,3 giây |

Hai bước bỏ qua không tính là đạt; script in riêng ở dòng "Bỏ qua":

- **1.3 Gợi ý phân loại:** `POST /api/ai/classify` trả 503 vì dịch vụ phân loại chưa có trong repo. Chờ #28, #30, #31.
- **1.15 Thống kê CS1:** Data API chưa có `GET /stats` (404). Chờ #22.

Điều kiện "2 lần liên tiếp không lỗi" của #34 đạt cho các bước đang kiểm được. Gợi ý phân loại và dashboard thống kê chưa kiểm chứng được cho tới khi các Issue trên xong.

## 3. Các bước script kiểm tra

Mỗi dòng là một kiểm tra trong script; mã và trạng thái so khớp chính xác, không phải chỉ "không lỗi".

| Bước | Kiểm tra |
|---|---|
| 1.1 SSO | 4 tài khoản (`sinhvien`, `truongphong`, `kythuatvien`, `quantri`) lấy token Keycloak, `GET /api/me` trả đúng username |
| 1.2 Thiết bị | `GET /api/assets/me` của sinh viên có thiết bị (`HAUI-LT-0001`); `GET /api/assets/bytag/{tag}` trả đúng id |
| 1.3 Phân loại | Bỏ qua, xem mục 2 |
| 1.4, 1.5 | Tạo bản nháp (201); `PUT /api/files/...` ảnh PNG (201); đăng ký tệp đính kèm (201) |
| 1.6 Gửi | `submit` trả `SUBMITTED`, cơ sở `CS1` |
| 1.7 Chặn chéo cơ sở | `truongphong_cs2` đọc phiếu CS1 nhận 404 |
| 1.8 | Trưởng phòng CS1 tiếp nhận; phân công `kythuatvien` trả `ASSIGNED` |
| 1.9 | Kỹ thuật viên nhận việc trả `IN_PROGRESS`; nhãn Snipe-IT thành "Đang sửa chữa" trong 40 giây (qua NATS, `asset-sync`) |
| 1.10 | Hoàn thành thiếu biên bản trả 422; có biên bản trả `RESOLVED` |
| 1.11 | Mở lại thiếu lý do trả 422; có lý do trả `IN_PROGRESS` và vẫn giao `kythuatvien`; hoàn thành lần 2 |
| 1.12 | Đóng trả `CLOSED`; nhãn Snipe-IT về lại nhãn ban đầu và ghi chú tài sản có số phiếu |
| 1.13 | Sinh viên đánh giá (200) |
| 1.14 Provenance | Đúng 11 sự kiện nghiệp vụ theo thứ tự (`CREATE_DRAFT`, `ATTACH`, `SUBMIT`, `ACCEPT`, `ASSIGN`, `START_PROGRESS`, `RESOLVE`, `REOPEN`, `RESOLVE`, `CLOSE`, `RATE`), `reopen_count = 1` |
| 1.15 | Sinh viên gọi `GET /api/data/stats` nhận 403 ở gateway; trưởng phòng được gateway cho qua; Grafana `/api/health` trả `database: ok`. Thống kê CS1 bỏ qua |
| 2.1 Từ chối | Thiếu lý do trả 422; có lý do trả `REJECTED` |
| 2.2 Không có asset_id | Phiếu chỉ có vị trí vẫn gửi được (`SUBMITTED`) |
| 2.3 Phân loại không phản hồi | Phân loại trả 503 nhưng phiếu ở bước 1.6 vẫn gửi được (ADR-05). Luật từ khoá dự phòng (#30) chưa có nên chưa kiểm |

## 4. Chưa nằm trong script này

- Gán kỹ thuật viên khác cơ sở (422) và lọc danh sách kỹ thuật viên theo cơ sở: có trong `scripts/test-data-api.py` (`make smoke`).
- Đóng phiếu khi `asset-sync` tắt rồi bật lại: có trong `scripts/test-assets-api.py` (`make smoke-assets`).
- Số liệu Prometheus của gateway, database và Data API: có trong `scripts/test-monitoring.py` (`make smoke-monitoring`).
- Snipe-IT không đổi khi phiếu bị từ chối: chưa có kiểm tra tự động.
- Giao diện trên trình duyệt: kiểm tra bằng tay theo `docs/manual-checks.md`.

## 5. Ghi chú

- Phiếu mẫu của `make seed` chưa có `workflow_instance_id`, nên thao tác quy trình trên phiếu mẫu trả 409. Script chỉ dùng phiếu tự tạo nên không bị ảnh hưởng; khi demo nên thao tác trên phiếu mới tạo.
- Script tạo phiếu mới mỗi lần chạy, không xoá dữ liệu.

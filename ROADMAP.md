<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Lộ trình

Tệp này ghi những gì đã phát hành và những việc dự kiến làm tiếp. Phần dự kiến chưa chạy
trong bản phát hành nào. Mỗi việc có Issue riêng; trạng thái mới nhất xem trên Issue đó.

## Đã phát hành

| Phiên bản | Ngày | Nội dung chính |
|---|---|---|
| v0.1.0 | 14/10/2026 | Open-Core chạy headless: Keycloak, APISIX, PostgreSQL, SeaweedFS, Flowable sau gateway có xác thực |
| v1.0.0 | 26/10/2026 | DX-Helpdesk chạy trọn vòng nghiệp vụ: SSO, báo hỏng kèm ảnh, định tuyến theo cơ sở, quy trình BPMN trên Flowable, tích hợp Snipe-IT qua NATS, gợi ý phân loại có luật dự phòng, giám sát bằng Prometheus và Grafana |

Chi tiết từng thay đổi ở [CHANGELOG.md](CHANGELOG.md).

## Dự kiến sau v1.0.0

Thứ tự trong bảng là thứ tự ưu tiên hiện tại, không phải cam kết ngày.

| Việc | Không gian | Issue |
|---|---|---|
| API thống kê theo cơ sở, để trang Thống kê có số liệu | D | [#22](https://github.com/HaUI-Libre/dx-lab/issues/22), [#27](https://github.com/HaUI-Libre/dx-lab/issues/27) |
| Định tuyến theo cơ sở bằng vùng PostGIS thay cho bảng ánh xạ vị trí | D | [#79](https://github.com/HaUI-Libre/dx-lab/issues/79) |
| Mã phiếu dạng DXL-NNNN và tra phiếu theo mã | D, ứng dụng | [#122](https://github.com/HaUI-Libre/dx-lab/issues/122) |
| Tách `portal.vue` thành component | H, ứng dụng | [#94](https://github.com/HaUI-Libre/dx-lab/issues/94) |
| Kiểm thử dịch vụ phân loại qua HTTP và trên tập kiểm tra tách riêng | I | [#142](https://github.com/HaUI-Libre/dx-lab/issues/142) |
| Bản đồ vị trí thiết bị (tùy chọn) | ứng dụng | [#80](https://github.com/HaUI-Libre/dx-lab/issues/80) |

Việc còn mở của bản phát hành hiện tại xem ở milestone
[v1.0.0](https://github.com/HaUI-Libre/dx-lab/milestone/4).

## Cách tham gia

- Người mới: chọn một Issue có nhãn
  [`good first issue`](https://github.com/HaUI-Libre/dx-lab/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22).
  Mỗi Issue này ghi bối cảnh, việc cần làm và điều kiện hoàn thành, không cần biết trước
  toàn bộ hệ thống.
- Muốn đề xuất việc mới cho lộ trình: mở Issue bằng mẫu *Đề xuất tính năng*, nêu bài toán
  trước khi nêu cách làm.
- Cách tạo nhánh, commit, mở PR: [CONTRIBUTING.md](CONTRIBUTING.md).

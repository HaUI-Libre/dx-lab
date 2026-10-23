<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Báo cáo kỹ thuật DX-Lab (#40, bản nháp)

Bản nháp nội dung để đội duyệt trước khi dàn trang thành PDF 8–10 trang. Số liệu lấy từ
repo tại thời điểm soạn; các phần ghi "chưa xong" phải cập nhật trước khi nộp.

## 1. Giới thiệu

Đề OLP PMNM 2026 yêu cầu xây dựng Hệ điều hành Chuyển đổi số bằng công nghệ lõi nguồn
mở (DX-OS Open-Core). DX-Lab dựng một Open-Core headless và chạy trên đó ứng dụng
DX-Helpdesk: báo hỏng và sửa chữa thiết bị CNTT ở 3 cơ sở của trường, nối với phần mềm
quản lý tài sản mà khách hàng đang dùng (giả lập bằng Snipe-IT) thay vì thay thế nó.

Mục tiêu: một trường hoặc đơn vị khác lấy mã về, chạy `make env && make up` là có nền
tảng; đổi ứng dụng nghiệp vụ không phải sửa Open-Core; đổi phần mềm tài sản chỉ phải
viết lại một adapter.

## 2. Kiến trúc Open-Core (Tầng 1)

| Thành phần | Vai trò |
|---|---|
| Keycloak 26.8 | SSO OIDC, 4 vai trò, thuộc tính `co_so` vào token |
| Apache APISIX 3.19 | Cửa ngõ duy nhất; xác thực JWKS, plugin `dxlab-roles`, quyền theo đường dẫn tệp |
| PostgreSQL 18.6 + PostGIS 3.6.4 | 3 database riêng (keycloak, flowable, dxdata) |
| Flowable REST 7.2 | Chạy quy trình BPMN 2.0 |
| SeaweedFS 4.48 | Ảnh và tệp đính kèm |
| NATS JetStream 2.15 | Trục sự kiện tích hợp |

Open-Core không có giao diện người dùng cuối (ADR-01). Mọi lời gọi từ Tầng 2, 3 đi qua
APISIX với token Keycloak (ADR-02). Compose chia profile: mặc định chỉ lõi và dịch vụ
của đội để chạy nhẹ; `integration` thêm Snipe-IT, MariaDB, dịch vụ tích hợp, NATS;
`monitoring` thêm Prometheus, Grafana (ADR-09).

*Hình: `docs/images/architecture-3-tier.svg`.*

## 3. Không gian H-P-D-I (Tầng 2)

| Không gian | Đã có |
|---|---|
| H – Con người | SSO, 4 vai trò, `co_so`; portal hồ sơ, nhóm, tài liệu phân quyền theo thư mục |
| P – Quy trình | BPMN tiếp nhận, từ chối, phân công, xử lý, nghiệm thu, mở lại; hàng đợi theo vai trò và cơ sở |
| D – Dữ liệu | Data API FastAPI theo OpenAPI 3; provenance, lịch sử sự kiện; trang thống kê (API thống kê chưa xong, #22) |
| I – Trí tuệ | Gợi ý phân loại trên giao diện; dịch vụ phân loại scikit-learn và luật dự phòng chưa xong (#28, #30, #31) |

## 4. Ứng dụng DX-Helpdesk (Tầng 3)

Nuxt 4 theo mô hình BFF: server Nuxt giữ token, trình duyệt chỉ có cookie phiên. Các
màn hình: thiết bị của tôi và báo hỏng kèm ảnh, hàng đợi, chi tiết ticket với nút theo
vai trò và trạng thái, lịch sử, đánh giá, portal, thống kê. Nút chỉ là gợi ý; Data API
kiểm tra lại vai trò, cơ sở, người được giao và trạng thái ở mỗi bước.

## 5. Luồng dữ liệu và tích hợp

1. Sinh viên đăng nhập; app lấy thiết bị của người đó qua `/api/assets/me`.
2. Báo hỏng: ảnh lên SeaweedFS qua `/api/files`, ticket qua `/api/data`. Khi gửi, Data
   API xác minh vị trí thiết bị trên Snipe-IT và suy ra cơ sở; không tin cơ sở do giao
   diện gửi; khởi tạo process trên Flowable.
3. Trưởng phòng cơ sở đó tiếp nhận và phân công; danh sách kỹ thuật viên lọc theo
   `co_so`, kiểm tra lại ở Data API qua service account Keycloak chỉ có quyền đọc.
4. Mỗi lần đổi trạng thái đã commit, Data API phát `dxlab.ticket.status_changed` lên
   NATS. Dịch vụ tích hợp nhận bằng durable consumer, đặt nhãn "Đang sửa chữa" khi bắt
   đầu, trả nhãn cũ và ghi biên bản vào ghi chú tài sản khi đóng. Dịch vụ dừng thì sự
   kiện chờ trong JetStream; lỗi Snipe-IT được thử lại (ADR-06, ADR-07).
5. Không có NATS hoặc Snipe-IT, quy trình vẫn chạy: báo hỏng bằng vị trí nhập tay, cập
   nhật tài sản ghi lỗi để thử lại.

*Hình: `docs/images/integration-architecture.svg`, `docs/images/helpdesk-workflow.svg`.*

## 6. AI (chưa xong)

Thiết kế (ADR-05): mô hình scikit-learn huấn luyện lúc build từ 160 mẫu tiếng Việt, gợi
ý loại và mức ưu tiên kèm từ khoá giải thích; luật từ khoá dự phòng khi mô hình lỗi;
người dùng chấp nhận hoặc sửa, trưởng phòng chốt ưu tiên. Giao diện đã gọi
`POST /api/ai/classify` và chịu được khi dịch vụ chưa chạy. Cần bổ sung: báo cáo
accuracy, F1, ma trận nhầm lẫn trên tập kiểm thử tách riêng (#28).

## 7. Giám sát

Prometheus thu metric từ APISIX, Keycloak, PostgreSQL, Data API, dịch vụ tích hợp và
NATS; Grafana hiện dashboard nạp qua provisioning. Không cổng metric nào mở ra máy;
exporter PostgreSQL dùng role `pg_monitor` thay vì superuser. Flowable REST 7.2 không
có endpoint Prometheus; số liệu quy trình lấy từ Data API.

## 8. Giấy phép và tính mở

- Mã của đội theo Apache-2.0, kèm NOTICE; mỗi tệp có header SPDX hoặc tệp `.license`,
  `reuse lint` đạt 121/121 tệp.
- Phần lõi chỉ dùng giấy phép OSI. Copyleft mạnh (Snipe-IT, Grafana AGPL; MariaDB,
  PostGIS GPL) chỉ ở dịch vụ chạy riêng, không liên kết với mã của đội.
- Giấy phép từng thành phần đọc tại đúng tag dùng trong compose; minh chứng `mongo:4.0`
  cho thấy giấy phép đổi theo phiên bản.
- Thay Vault, MongoDB, n8n, Redpanda, ImmuDB trong stack gợi ý của đề vì giấy phép không
  được OSI chấp thuận.
- Chuẩn mở: OIDC, BPMN 2.0, OpenAPI 3, GeoJSON, Prometheus exposition format.
- Đóng góp theo DCO; gitleaks quét toàn lịch sử không có secret.

## 9. Kiểm thử và chất lượng

- 31 test Python không cần stack; `make smoke` khoảng 110 kiểm tra trên stack thật,
  gồm cả các trường hợp bị chặn (sai cơ sở, thiếu lý do, vượt thư mục).
- CI 5 check bắt buộc trước khi merge, trong đó một job dựng toàn bộ stack trên máy
  sạch. Job này bắt được lỗi chỉ lộ ra trên máy chưa có dữ liệu cũ (#89, #98).
- Chi tiết: `docs/testing.md`, `docs/audit.md`.

## 10. Đánh giá, hạn chế, hướng phát triển

| Hạng mục | Tình trạng |
|---|---|
| Chuỗi demo tích hợp SSO → thiết bị → báo hỏng → định tuyến → phân công → xử lý → nghiệm thu → Snipe-IT | Đã chạy |
| Thống kê theo cơ sở | Trang đã có, chờ API #22 |
| Dịch vụ phân loại | Chờ #28, #30, #31 |
| Định tuyến theo vùng bằng PostGIS | Chờ #79 |
| Seed theo UUID người dùng | Chờ #84 |

Hạn chế đã biết: Flowable hoàn thành task trước khi Data API commit, chưa có bước bù khi
commit lỗi; route kiểm thử Flowable cho admin vẫn mở để chạy bộ kiểm thử quy trình.

<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Hỏi đáp chuẩn bị cho Hội đồng (#42, bản nháp)

Mỗi câu có người trả lời chính. Câu trả lời ngắn để nói trong 30–60 giây; chi tiết nằm
ở tài liệu dẫn kèm. Câu hỏi ở mục 13 của đề cần được bổ sung khi đội đối chiếu với đề.

## Giấy phép

**Vì sao chọn Apache-2.0?** (Trung)
Để trường hoặc đơn vị khác lấy nền tảng về, tích hợp với hệ thống sẵn có của họ và dùng
cả cho mục đích thương mại mà không bị buộc mở mã phần của họ; người đóng góp được bảo
vệ bằng điều khoản cấp quyền sáng chế. Đã so sánh với MIT, GPL-3.0, AGPL-3.0.
`docs/license-decision.md` mục 1.

**Snipe-IT và Grafana dùng AGPL-3.0, sao vẫn dùng được trong dự án Apache-2.0?** (Trung)
Cả hai chạy như dịch vụ riêng trong container riêng, giao tiếp qua HTTP; mã của đội
không liên kết với chúng và đội không sửa mã của chúng. Nghĩa vụ AGPL gắn với chính
phần mềm đó, không lan sang mã Apache-2.0 của đội. Snipe-IT đóng vai hệ thống của khách
hàng, nằm ngoài DX-OS; dashboard Grafana là tệp JSON nạp qua provisioning. Nếu sau này
sửa mã Snipe-IT thì phải công bố phần sửa theo AGPL. ADR-06, `license-decision.md` mục 5.

**Vì sao thay Vault, MongoDB, n8n, Redpanda, ImmuDB trong stack gợi ý của đề?** (Trung)
Đề ghi bảng là ví dụ, đội tự chọn. Năm thành phần này dùng giấy phép không được OSI
chấp thuận: Vault và ImmuDB BUSL-1.1, MongoDB SSPL, n8n Sustainable Use License,
Redpanda BSL 1.1. Thay bằng: secret trong `.env` sinh ngẫu nhiên, PostgreSQL, Flowable,
NATS JetStream, bảng `ticket_events`. `license-decision.md` mục 8.

**Minh chứng `mongo:4.0`?** (Trung)
Image `mongo:4.0` vẫn kéo về được, nhưng bản cuối của nhánh 4.0 (r4.0.28) đã theo SSPL;
mọi bản MongoDB từ 16/10/2018 đều SSPL. Ví dụ này cho thấy phải đọc giấy phép tại đúng
tag, không dựa vào tên hay tuổi của image. `license-decision.md` mục 7.

**DCO khác CLA thế nào?** (Linh)
DCO là lời xác nhận trong từng commit (`Signed-off-by`) rằng người đóng góp có quyền nộp
mã theo giấy phép của dự án; không chuyển nhượng bản quyền. CLA là hợp đồng ký riêng,
thường cấp hoặc chuyển quyền cho chủ dự án. Đội dùng DCO để đóng góp nhẹ thủ tục và bản
quyền vẫn thuộc người viết. `CONTRIBUTING.md` mục 6.

**Làm sao chắc không lộ secret và tệp nào cũng có giấy phép?** (Linh)
CI chạy gitleaks trên toàn bộ lịch sử và `reuse lint` trên mọi PR; cả hai là check bắt
buộc. Kết quả gần nhất: 121/121 tệp có thông tin giấy phép, không phát hiện secret.
`docs/audit.md`.

## Kiến trúc

**7 lớp của đề ánh xạ vào 3 tầng thế nào?** (Trung)
Lớp 1 giao diện ở Tầng 3; lớp 2 cửa ngõ và ATTT (APISIX, Keycloak) ở Tầng 1; lớp 3 logic
nghiệp vụ (Data API, tích hợp tài sản) ở Tầng 2; lớp 4 quy trình (Flowable) và DevSecOps
(CI) ở Tầng 1; lớp 5 truyền phát (NATS, `ticket_events`, SeaweedFS) ở Tầng 1–2; lớp 6
phân tích, không gian, trí tuệ (PostGIS, thống kê, phân loại) ở Tầng 1–2; lớp 7 giám
sát (Prometheus, Grafana) nằm ngoài 3 tầng, là phần vận hành. `architecture.md` mục 2.

**Vì sao không thêm vai trò theo cơ sở (ví dụ `ROLE_LAB_MANAGER_CS1`)?** (Nam Anh)
Vai trò mô tả việc được làm, cơ sở mô tả phạm vi. Gộp hai thứ thì số vai trò nhân theo
số cơ sở, và mỗi cơ sở mới phải sửa realm, BPMN, gateway. Đội giữ 4 vai trò và thêm
thuộc tính `co_so` trong Keycloak, đưa vào claim của token; Data API lọc theo claim và
không tin giá trị cơ sở do giao diện gửi; chỉ admin sửa được `co_so`.

**Vì sao Open-Core không có giao diện?** (Trung)
Tầng 1 là hạ tầng dùng chung; đổi ứng dụng nghiệp vụ không phải sửa Open-Core. Mọi lời
gọi từ Tầng 2, 3 đi qua APISIX với token Keycloak. ADR-01, ADR-02.

**Nếu Snipe-IT sập thì sao?** (Nam Anh)
Người dùng vẫn báo hỏng bằng vị trí nhập tay. Cập nhật nhãn tài sản đi qua NATS
JetStream với durable consumer: dịch vụ tích hợp dừng thì sự kiện chờ, bật lại vẫn xử
lý; lỗi Snipe-IT được thử lại. `make smoke-assets` thử đúng trường hợp này. ADR-07.

**AI có tự quyết định gì không?** (Nam Anh)
Không. Dịch vụ chỉ gợi ý loại và mức ưu tiên kèm từ khoá giải thích; người báo bấm chấp
nhận hoặc tự chọn; trưởng phòng chốt mức ưu tiên khi phân công. Dịch vụ lỗi thì form
vẫn gửi. ADR-05.

## Kỹ thuật

**Làm sao chứng minh build được từ mã nguồn?** (Linh)
CI job "Stack từ volume trống" dựng toàn bộ stack trên runner sạch cho mọi PR chạm hạ
tầng: `make env`, `docker compose build`, `make up`, `make smoke`. Đội từng có hai lỗi
chỉ lộ ra trên máy sạch (#89, #98); job này được thêm để bắt loại lỗi đó. #38 ghi kết quả
build trên máy chưa từng chạy dự án.

**Phân quyền kiểm tra ở đâu?** (Nam Anh)
Ở gateway (vai trò, quyền theo đường dẫn tệp) và ở Data API (chủ ticket, cơ sở, người
được giao, trạng thái). Nút trên giao diện chỉ là gợi ý. `make smoke` gọi thẳng API để
thử các trường hợp bị chặn.

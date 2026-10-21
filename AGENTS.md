<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Hướng dẫn làm việc trong DX-Lab

## Mục tiêu và nguồn tham chiếu

- Đây là bài dự thi PMNM HaUI 2026 về DX-OS Open-Core. Sản phẩm minh họa là DX-Helpdesk: báo hỏng và sửa chữa thiết bị CNTT, tích hợp với phần mềm quản lý tài sản có sẵn của khách hàng (giả lập bằng Snipe-IT), định tuyến ticket theo cơ sở, cập nhật trạng thái tài sản về hệ thống đó.
- Trước khi sửa một chức năng, đọc issue liên quan bằng `gh issue view <số> --repo HaUI-Libre/dx-lab --json title,body,comments`; kiểm tra đầu vào, đầu ra, điều kiện hoàn thành và phụ thuộc. Dùng `gh issue list --repo HaUI-Libre/dx-lab --state open` khi cần tìm issue. Nếu GitHub không truy cập được, dùng tài liệu trong repo và nêu rõ phần bối cảnh còn thiếu; không đoán nội dung issue.
- Đọc `README.md`, `docs/architecture.md` và đặc tả nghiệp vụ `docs/usecases.md` cho thay đổi liên quan kiến trúc hoặc nghiệp vụ. `CONTRIBUTING.md` quy định cách đóng góp; `docs/dependencies.md` ghi thành phần và giấy phép.
- Bám phạm vi và điều kiện hoàn thành của issue. Phân biệt yêu cầu trong đặc tả với phần đã triển khai; không mô tả tính năng dự kiến như tính năng đang chạy.

## Ranh giới kiến trúc

- Tầng 1 là Open-Core headless: Keycloak (OIDC/SSO, vai trò), Apache APISIX (gateway), PostgreSQL (PostGIS từ M3), SeaweedFS, Flowable và NATS (từ M3). Không thêm UI người dùng cuối vào tầng này.
- Tầng 2 gồm H (người dùng, nhóm, tài liệu), P (quy trình), D (dữ liệu, provenance, dashboard) và I (phân loại, gợi ý ưu tiên bằng scikit-learn; không dùng LLM, RAG đã bỏ), cùng dịch vụ tích hợp tài sản. Tầng 3 là ứng dụng DX-Helpdesk.
- Snipe-IT và MariaDB là hệ thống của khách hàng, nằm ngoài DX-OS. Chỉ dịch vụ tích hợp tài sản gọi Snipe-IT qua REST API `/api/v1`; không đọc database và không sửa mã Snipe-IT.
- UI Nuxt và các luồng nghiệp vụ tầng trên gọi dịch vụ qua APISIX với token Keycloak; không kết nối trực tiếp từ UI đến PostgreSQL, Flowable, SeaweedFS hoặc dịch vụ AI. Giữ ranh giới `/api/data`, `/api/workflow`, `/api/files`, `/api/ai`, `/api/assets` khi triển khai tích hợp.
- Compose chia profile: mặc định là lõi và dịch vụ của đội, `integration` (Snipe-IT, MariaDB, tích hợp, NATS), `monitoring` (Prometheus, Grafana); service mặc định không phụ thuộc profile khác. Đặt cấu hình Open-Core ở `core/`, Data API FastAPI và dữ liệu mẫu ở `data/`, dịch vụ AI ở `ai/`, ứng dụng Nuxt ở `app/`, sơ đồ/BPMN/tài liệu ở `docs/`. Khi thay đổi hợp đồng giữa các tầng, cập nhật cả bên gọi, bên cung cấp và tài liệu liên quan.

## Nghiệp vụ DX-Helpdesk

- Giữ bốn vai trò trong đặc tả: `ROLE_STUDENT`, `ROLE_TECHNICIAN`, `ROLE_LAB_MANAGER`, `ROLE_ADMIN`. Kiểm tra quyền ở API/dịch vụ, không chỉ ẩn nút trên giao diện. Sinh viên tạo và theo dõi ticket của mình; kỹ thuật viên xử lý và lập biên bản; quản lý phân công, nghiệm thu và xem dashboard; admin cấu hình nền tảng. Không thêm vai trò theo cơ sở: kỹ thuật viên và quản lý có user attribute `co_so` trong Keycloak, ánh xạ vào claim `co_so`; Data API lọc hàng đợi theo claim này, không tin giá trị cơ sở do giao diện gửi.
- Vòng đời ticket: `DRAFT -> SUBMITTED -> ASSIGNED -> IN_PROGRESS -> RESOLVED -> CLOSED`; từ chối chỉ ở bước tiếp nhận (`SUBMITTED` sang `REJECTED`, kết thúc); mở lại chỉ ở bước nghiệm thu (`RESOLVED` về `IN_PROGRESS`, giao lại kỹ thuật viên cũ, lịch sử ghi `REOPEN`). Cả hai bắt buộc có lý do. Quyền thực hiện và điều kiện của mỗi chuyển trạng thái phải phù hợp BPMN/Flowable; lưu lịch sử xử lý.
- Dữ liệu ticket cần metadata/provenance tối thiểu `source`, `created_by`, `created_at`, `updated_at`. Tệp đính kèm đi qua tuyến lưu trữ, không nhúng vào dữ liệu ticket. Giữ trạng thái ticket và process instance nhất quán khi tích hợp Data API với Flowable.
- AI chỉ đưa ra gợi ý phân loại/ưu tiên có giải thích; người dùng xác nhận hoặc chỉnh trước khi gửi. Có đường fallback rule-based khi dịch vụ phân loại không sẵn sàng. Không để gợi ý AI tự quyết định quyền, mức ưu tiên cuối cùng hoặc chuyển trạng thái quy trình.
- Khi xây dựng luồng demo, kiểm tra chuỗi SSO -> thiết bị của tôi (từ Snipe-IT) -> báo hỏng kèm ảnh -> định tuyến theo cơ sở -> quản lý phân công -> kỹ thuật viên xử lý -> quản lý nghiệm thu -> Snipe-IT cập nhật trạng thái -> dashboard; kiểm tra thêm nhánh từ chối, mở lại và AI fallback khi phạm vi issue liên quan.

## Cách triển khai và kiểm tra

- Repo phát triển theo milestone. Kiểm tra tệp, service và trạng thái chạy thực tế trước khi dùng lệnh hoặc khẳng định một tính năng đã hoạt động; không suy từ danh sách thành phần dự kiến trong README.
- Dùng `make check` cho kiểm tra cục bộ hiện có (SPDX). Chạy test phù hợp với phần thay đổi khi các bộ test của `app/`, `data/`, `ai/` hoặc tích hợp được thêm vào; báo rõ lệnh đã chạy và phần chưa kiểm chứng. Với thay đổi Compose, kiểm tra cấu hình và khởi động service liên quan nếu môi trường cho phép.
- Mọi tệp mã/tài liệu mới cần SPDX header theo `CONTRIBUTING.md`. Không commit `.env`, token, mật khẩu, khóa hay dữ liệu nhạy cảm; biến cấu hình mới phải có giá trị giả trong `.env.example`.
- Trước khi thêm dependency, kiểm tra giấy phép và ghi tên, phiên bản, vai trò vào `docs/dependencies.md`. Mọi thành phần lõi của hệ thống, kể cả dịch vụ chạy riêng, đều được đội chọn có giấy phép OSI. Mã nguồn trong repo và thư viện liên kết trực tiếp phải có giấy phép được OSI chấp thuận, tương thích Apache-2.0; thành phần chạy riêng như dịch vụ độc lập tuân thủ giấy phép riêng của dịch vụ đó.
- Giữ thay đổi gọn theo một issue, cập nhật README/tài liệu khi hành vi hoặc cách chạy thay đổi. Không sửa mã nguồn thư viện bên ngoài trong repo.

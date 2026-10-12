<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Hướng dẫn làm việc trong DX-Lab

## Mục tiêu và nguồn tham chiếu

- Đây là bài dự thi PMNM HaUI 2026 về DX-OS Open-Core. Sản phẩm minh họa là DX-Helpdesk cho việc tiếp nhận và xử lý yêu cầu hỗ trợ CNTT/phòng máy.
- Trước khi sửa một chức năng, đọc issue liên quan bằng `gh issue view <số> --repo HaUI-Libre/dx-lab --json title,body,comments`; kiểm tra đầu vào, đầu ra, điều kiện hoàn thành và phụ thuộc. Dùng `gh issue list --repo HaUI-Libre/dx-lab --state open` khi cần tìm issue. Nếu GitHub không truy cập được, dùng tài liệu trong repo và nêu rõ phần bối cảnh còn thiếu; không đoán nội dung issue.
- Đọc `README.md`, `docs/architecture.md` và đặc tả nghiệp vụ `DX-Helpdesk - Dac ta nghiep vu DX-OS (docs_usecases.md).docx` cho thay đổi liên quan kiến trúc hoặc nghiệp vụ. `CONTRIBUTING.md` quy định cách đóng góp; `docs/dependencies.md` ghi thành phần và giấy phép.
- Bám phạm vi và điều kiện hoàn thành của issue. Phân biệt yêu cầu trong đặc tả với phần đã triển khai; không mô tả tính năng dự kiến như tính năng đang chạy.

## Ranh giới kiến trúc

- Tầng 1 là Open-Core headless: Keycloak (OIDC/SSO, vai trò), Apache APISIX (gateway), PostgreSQL, SeaweedFS và Flowable. Không thêm UI người dùng cuối vào tầng này.
- Tầng 2 gồm H (người dùng, nhóm, tài liệu), P (quy trình), D (dữ liệu, provenance, dashboard) và I (phân loại, gợi ý, RAG). Tầng 3 là ứng dụng DX-Helpdesk.
- UI Nuxt và các luồng nghiệp vụ tầng trên gọi dịch vụ qua APISIX với token Keycloak; không kết nối trực tiếp từ UI đến PostgreSQL, Flowable, SeaweedFS hoặc dịch vụ AI. Giữ ranh giới `/api/data`, `/api/workflow`, `/api/files`, `/api/ai` khi triển khai tích hợp.
- Đặt cấu hình Open-Core ở `core/`, Data API FastAPI và dữ liệu mẫu ở `data/`, dịch vụ AI ở `ai/`, ứng dụng Nuxt ở `app/`, sơ đồ/BPMN/tài liệu ở `docs/`. Khi thay đổi hợp đồng giữa các tầng, cập nhật cả bên gọi, bên cung cấp và tài liệu liên quan.

## Nghiệp vụ DX-Helpdesk

- Giữ bốn vai trò trong đặc tả: `ROLE_STUDENT`, `ROLE_TECHNICIAN`, `ROLE_LAB_MANAGER`, `ROLE_ADMIN`. Kiểm tra quyền ở API/dịch vụ, không chỉ ẩn nút trên giao diện. Sinh viên tạo và theo dõi ticket của mình; kỹ thuật viên xử lý và lập biên bản; quản lý phân công, nghiệm thu và xem dashboard; admin cấu hình nền tảng.
- Vòng đời ticket: `DRAFT -> SUBMITTED -> ASSIGNED -> IN_PROGRESS -> RESOLVED -> CLOSED`; nhánh từ chối từ `SUBMITTED` sang `REJECTED`. Quyền thực hiện và điều kiện của mỗi chuyển trạng thái phải phù hợp BPMN/Flowable; lưu lịch sử xử lý và lý do từ chối.
- Dữ liệu ticket cần metadata/provenance tối thiểu `source`, `created_by`, `created_at`, `updated_at`. Tệp đính kèm đi qua tuyến lưu trữ, không nhúng vào dữ liệu ticket. Giữ trạng thái ticket và process instance nhất quán khi tích hợp Data API với Flowable.
- AI chỉ đưa ra gợi ý phân loại/ưu tiên có giải thích; người dùng xác nhận hoặc chỉnh trước khi gửi. Có đường fallback rule-based khi dịch vụ AI/LLM không sẵn sàng. Không để gợi ý AI tự quyết định quyền, mức ưu tiên cuối cùng hoặc chuyển trạng thái quy trình.
- Khi xây dựng luồng demo, kiểm tra chuỗi SSO -> tạo ticket kèm ảnh -> quản lý phân công -> kỹ thuật viên xử lý -> quản lý nghiệm thu -> dashboard; kiểm tra thêm nhánh từ chối và AI fallback khi phạm vi issue liên quan.

## Cách triển khai và kiểm tra

- Repo phát triển theo milestone. Kiểm tra tệp, service và trạng thái chạy thực tế trước khi dùng lệnh hoặc khẳng định một tính năng đã hoạt động; không suy từ danh sách thành phần dự kiến trong README.
- Dùng `make check` cho kiểm tra cục bộ hiện có (SPDX). Chạy test phù hợp với phần thay đổi khi các bộ test của `app/`, `data/`, `ai/` hoặc tích hợp được thêm vào; báo rõ lệnh đã chạy và phần chưa kiểm chứng. Với thay đổi Compose, kiểm tra cấu hình và khởi động service liên quan nếu môi trường cho phép.
- Mọi tệp mã/tài liệu mới cần SPDX header theo `CONTRIBUTING.md`. Không commit `.env`, token, mật khẩu, khóa hay dữ liệu nhạy cảm; biến cấu hình mới phải có giá trị giả trong `.env.example`.
- Trước khi thêm dependency, kiểm tra giấy phép và ghi tên, phiên bản, vai trò vào `docs/dependencies.md`; ưu tiên thành phần nguồn mở có giấy phép được OSI chấp thuận theo quy định repo.
- Giữ thay đổi gọn theo một issue, cập nhật README/tài liệu khi hành vi hoặc cách chạy thay đổi. Không sửa mã nguồn thư viện bên ngoài trong repo.

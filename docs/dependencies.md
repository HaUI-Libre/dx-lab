<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Bảng thành phần phụ thuộc và giấy phép

Mọi thành phần bên ngoài phải được ghi tại đây trước khi merge. Chỉ dùng giấy
phép được OSI chấp thuận cho phần lõi sản phẩm. Cột **Phiên bản** ghi đúng phiên
bản/tag image đang dùng trong repo.

## Tầng 1 – Open-Core

| Thành phần | Phiên bản | Giấy phép | Vai trò | Nguồn |
|---|---|---|---|---|
| Keycloak | _(chốt ở M1)_ | Apache-2.0 | Identity, SSO, RBAC | https://github.com/keycloak/keycloak |
| Apache APISIX | _(chốt ở M1)_ | Apache-2.0 | API Gateway, xác thực JWT | https://github.com/apache/apisix |
| PostgreSQL | _(chốt ở M1)_ | PostgreSQL License | Dữ liệu cấu trúc | https://www.postgresql.org |
| pgvector | _(chốt ở M3)_ | PostgreSQL License | Tìm kiếm véc-tơ | https://github.com/pgvector/pgvector |
| SeaweedFS | _(chốt ở M1)_ | Apache-2.0 | Lưu trữ tệp/đối tượng | https://github.com/seaweedfs/seaweedfs |
| Flowable | _(chốt ở M1)_ | Apache-2.0 | Workflow engine (BPMN) | https://github.com/flowable/flowable-engine |

## Tầng 2 / 3

| Thành phần | Phiên bản | Giấy phép | Vai trò | Nguồn |
|---|---|---|---|---|
| FastAPI | | MIT | Data API | https://github.com/fastapi/fastapi |
| Nuxt | | MIT | Giao diện H-P-D-I, ứng dụng | https://github.com/nuxt/nuxt |
| scikit-learn | | BSD-3-Clause | Phân loại / ưu tiên yêu cầu | https://github.com/scikit-learn/scikit-learn |
| Ollama | | MIT | Chạy LLM nội bộ | https://github.com/ollama/ollama |
| Mô hình LLM | | _(kiểm tra từng bản)_ | RAG | |

## Công cụ phát triển (không đóng gói trong sản phẩm)

| Công cụ | Giấy phép | Vai trò |
|---|---|---|
| gitleaks | MIT | Quét secret trong CI |
| Docker Compose | Apache-2.0 | Dựng môi trường |

## Đã cân nhắc nhưng không dùng

| Thành phần | Lý do |
|---|---|
| n8n | Sustainable Use License, không phải giấy phép OSI |
| Directus | Business Source License, không phải giấy phép OSI |

## Nguồn dữ liệu

| Nguồn | Giấy phép / quyền sử dụng | Dùng cho |
|---|---|---|
| _(bổ sung ở M2)_ | | |

<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Bảng thành phần phụ thuộc và giấy phép

Mọi thành phần bên ngoài phải được ghi tại đây trong cùng PR thêm nó. Phần lõi chỉ
dùng giấy phép được OSI chấp thuận. Cột **Phiên bản** ghi đúng tag image hoặc phiên
bản thư viện đang dùng trong repo. Cột **Cách dùng** cho biết thành phần chạy như
dịch vụ riêng hay được liên kết vào mã của đội, vì điều đó quyết định nghĩa vụ giấy
phép. Lý do chọn và nguồn kiểm tra giấy phép theo từng phiên bản:
[license-decision.md](license-decision.md).

## Tầng 1 – Open-Core (đang chạy)

| Thành phần | Phiên bản | Giấy phép | Vai trò | Cách dùng | Nguồn |
|---|---|---|---|---|---|
| Keycloak | `quay.io/keycloak/keycloak:26.8.0` | Apache-2.0 | Identity, SSO, RBAC | Dịch vụ riêng; realm cấu hình bằng [realm-dxlab.json](../core/identity/realm-dxlab.json) | https://github.com/keycloak/keycloak |
| Apache APISIX | `apache/apisix:3.19.0-debian` | Apache-2.0 | API Gateway, xác thực JWT | Dịch vụ riêng; route ở [apisix.yaml](../core/gateway/apisix.yaml), plugin của đội ở [dxlab-roles.lua](../core/gateway/plugins/apisix/plugins/dxlab-roles.lua) | https://github.com/apache/apisix |
| PostgreSQL | `postgres:18.6-alpine` | PostgreSQL | Dữ liệu cấu trúc | Dịch vụ riêng, SQL; khởi tạo bằng [01-create-databases.sh](../core/postgres/init/01-create-databases.sh) | https://www.postgresql.org |
| SeaweedFS | `chrislusf/seaweedfs:4.48` | Apache-2.0 | Lưu trữ tệp | Dịch vụ riêng, HTTP filer sau gateway | https://github.com/seaweedfs/seaweedfs |
| Flowable | `flowable/flowable-rest:7.2.0` | Apache-2.0 | Workflow engine (BPMN), REST headless | Dịch vụ riêng, REST sau gateway | https://github.com/flowable/flowable-engine |

## Dự kiến (hướng tích hợp tài sản)

Chưa có trong `docker-compose.yml`. Phiên bản chốt khi tích hợp và phải kiểm tra lại
giấy phép tại đúng tag đó.

| Thành phần | Phiên bản | Giấy phép | Vai trò | Cách dùng dự kiến | Nguồn |
|---|---|---|---|---|---|
| PostGIS | _(chốt ở B4)_ | GPL-2.0-or-later | Dữ liệu vị trí, định tuyến theo cơ sở | Extension trong PostgreSQL, gọi qua SQL | https://postgis.net |
| Snipe-IT | _(chốt ở M2)_ | AGPL-3.0 | Giả lập hệ thống quản lý tài sản của khách hàng | Dịch vụ riêng, REST API, không sửa mã | https://github.com/grokability/snipe-it |
| MariaDB | _(chốt ở M2, compose chính thức của Snipe-IT dùng `mariadb:11.4.7`)_ | GPL-2.0 | Database của Snipe-IT | Dịch vụ riêng, chỉ Snipe-IT kết nối; DX-Lab không đọc | https://github.com/MariaDB/server |
| NATS Server | _(chốt ở M2)_ | Apache-2.0 | Trục sự kiện tích hợp | Dịch vụ riêng | https://github.com/nats-io/nats-server |
| Prometheus | _(chốt ở M3)_ | Apache-2.0 | Thu thập metric | Dịch vụ riêng | https://github.com/prometheus/prometheus |
| Grafana | _(chốt ở M3)_ | AGPL-3.0 | Dashboard giám sát | Dịch vụ riêng, dashboard nạp qua provisioning | https://github.com/grafana/grafana |
| postgres_exporter | _(chốt ở M3)_ | Apache-2.0 | Metric PostgreSQL | Dịch vụ riêng | https://github.com/prometheus-community/postgres_exporter |
| prometheus-nats-exporter | _(chốt ở M3)_ | Apache-2.0 | Metric NATS | Dịch vụ riêng | https://github.com/nats-io/prometheus-nats-exporter |

## Tầng 3 – Ứng dụng (đang chạy)

| Thành phần | Phiên bản | Giấy phép | Vai trò | Cách dùng | Nguồn |
|---|---|---|---|---|---|
| Nuxt | `4.5.2` | MIT | Khung ứng dụng DX-Helpdesk | Thư viện trong `app/`, ghim trong [package.json](../app/package.json) và `package-lock.json` | https://github.com/nuxt/nuxt |
| Vue | `3.5.43` | MIT | Giao diện | Thư viện, kéo theo bởi Nuxt | https://github.com/vuejs/core |
| openid-client | `6.8.8` | MIT | Luồng OIDC authorization code + PKCE, làm mới token | Thư viện phía server trong `app/server/`; kéo theo `jose`, `oauth4webapi` (MIT, cùng tác giả) | https://github.com/panva/openid-client |
| Node.js | `node:24.21.0-alpine` | MIT | Môi trường chạy ứng dụng | Image nền để dựng và chạy `app/` ([Dockerfile](../app/Dockerfile)) | https://github.com/nodejs/node |

## Tầng 2 / 3 (dự kiến)

| Thành phần | Phiên bản | Giấy phép | Vai trò | Cách dùng dự kiến | Nguồn |
|---|---|---|---|---|---|
| FastAPI | _(chốt ở M2)_ | MIT | Data API | Thư viện trong `data/` | https://github.com/fastapi/fastapi |
| scikit-learn | _(chốt ở M3)_ | BSD-3-Clause | Phân loại, gợi ý mức ưu tiên | Thư viện trong `ai/` | https://github.com/scikit-learn/scikit-learn |
| prometheus_client (Python) | _(chốt ở M3)_ | Apache-2.0 | Xuất metric từ Data API, dịch vụ tích hợp | Thư viện | https://github.com/prometheus/client_python |
| Leaflet | _(chốt ở M3)_ | BSD-2-Clause | Bản đồ vị trí thiết bị | Thư viện đóng gói trong `app/` | https://github.com/Leaflet/Leaflet |

## Nguồn dữ liệu

| Nguồn | Giấy phép / quyền sử dụng | Dùng cho | Ghi chú & Nguồn gốc |
|---|---|---|---|
| Dữ liệu mẫu DX-Helpdesk | Apache-2.0 | Cây vị trí, tài sản, ticket, tập huấn luyện phân loại AI | Tọa độ và ranh giới 3 cơ sở là ước lượng, do đội tự xác định để minh họa |

## Công cụ phát triển (không phân phối kèm sản phẩm)

| Công cụ | Phiên bản | Giấy phép | Vai trò |
|---|---|---|---|
| Docker Engine (Moby) | 24+ | Apache-2.0 | Chạy container |
| Docker Compose plugin | v2.17+ | Apache-2.0 | Dựng môi trường |
| reuse | 6.2.0 | GPL-3.0-or-later | Kiểm tra giấy phép từng tệp trong CI và `make check` |
| gitleaks | 8.24.2 | MIT | Quét secret trong CI |
| actions/checkout, actions/setup-python | v5, v6 | MIT | Bước CI trên GitHub Actions |
| amannn/action-semantic-pull-request | v6.1.1 | MIT | Kiểm tra tiêu đề PR theo Conventional Commits |

Docker Desktop không được yêu cầu vì không phải phần mềm nguồn mở.

## Đã cân nhắc nhưng không dùng

| Thành phần | Giấy phép | Lý do |
|---|---|---|
| HashiCorp Vault | BUSL-1.1 | Không phải giấy phép OSI |
| MongoDB | SSPL-1.0 (mọi bản từ 16/10/2018) | Không phải giấy phép OSI |
| Redpanda | BSL 1.1 | Không phải giấy phép OSI; dùng NATS |
| immudb | BUSL-1.1 | Không phải giấy phép OSI |
| n8n | Sustainable Use License | Không phải giấy phép OSI; dùng Flowable |
| Directus | BSL 1.1 (v10–v11), MSCL-1.0 (v12) | Không phải giấy phép OSI; dùng Data API |
| Qwen2.5-3B, Qwen2.5-72B | Qwen Research License, Qwen License | Giấy phép riêng của mô hình |
| Llama | Llama Community License | Giấy phép riêng của mô hình |
| Gemma | Gemma Terms of Use | Giấy phép riêng của mô hình |

## Đã hủy do bỏ RAG khỏi phạm vi

| Thành phần | Giấy phép | Vai trò cũ |
|---|---|---|
| ~~Ollama~~ | MIT | Chạy LLM nội bộ |
| ~~Mô hình LLM (`qwen2.5:1.5b`)~~ | Apache-2.0 | RAG hỏi đáp tài liệu |
| ~~pgvector~~ | PostgreSQL | Tìm kiếm véc-tơ cho RAG |

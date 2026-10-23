<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Bảng thành phần phụ thuộc và giấy phép

Mọi thành phần bên ngoài phải được ghi tại đây trong cùng PR thêm nó. Mọi
thành phần lõi của hệ thống, kể cả dịch vụ chạy riêng, đều được đội chọn có
giấy phép OSI. Mã nguồn trong repo và thư viện liên kết trực tiếp phải có
giấy phép tương thích Apache-2.0; phần mềm chạy riêng như dịch vụ độc lập
tuân thủ giấy phép riêng của dịch vụ đó. Không chỉnh sửa mã nguồn của phần
mềm bên ngoài khi giấy phép không cho phép. Cột **Phiên bản** ghi đúng tag
image hoặc phiên bản thư viện đang dùng trong repo. Cột **Cách dùng** cho
biết thành phần chạy như dịch vụ riêng hay được liên kết vào mã của đội,
vì điều đó quyết định nghĩa vụ giấy phép. Lý do chọn và nguồn kiểm tra
giấy phép theo từng phiên bản: [license-decision.md](license-decision.md).

## Tầng 1 – Open-Core (đang chạy)

| Thành phần | Phiên bản | Giấy phép | Vai trò | Cách dùng | Nguồn |
|---|---|---|---|---|---|
| Keycloak | `quay.io/keycloak/keycloak:26.8.0` | Apache-2.0 | Identity, SSO, RBAC | Dịch vụ riêng; realm cấu hình bằng [realm-dxlab.json](../core/identity/realm-dxlab.json) | https://github.com/keycloak/keycloak |
| Apache APISIX | `apache/apisix:3.19.0-debian` | Apache-2.0 | API Gateway, xác thực JWT | Dịch vụ riêng; route ở [apisix.yaml](../core/gateway/apisix.yaml), plugin của đội ở [dxlab-roles.lua](../core/gateway/plugins/apisix/plugins/dxlab-roles.lua) | https://github.com/apache/apisix |
| PostgreSQL | 18.6, trong image `postgis/postgis:18-3.6-alpine` ghim digest | PostgreSQL | Dữ liệu cấu trúc | Dịch vụ riêng, SQL; khởi tạo bằng [01-create-databases.sh](../core/postgres/init/01-create-databases.sh) | https://www.postgresql.org |
| PostGIS | 3.6.4 | GPL-2.0-or-later | Dữ liệu vị trí, định tuyến theo cơ sở (#79) | Extension trong `dxdata`, bật bằng [02-enable-postgis.sh](../core/postgres/init/02-enable-postgis.sh); gọi qua SQL, mã của đội không liên kết | https://postgis.net |
| docker-postgis | commit `148ce95` | MIT | Dockerfile của image `postgis/postgis` | Image tải sẵn, không build lại | https://github.com/postgis/docker-postgis |
| SeaweedFS | `chrislusf/seaweedfs:4.48` | Apache-2.0 | Lưu trữ tệp | Dịch vụ riêng, HTTP filer sau gateway | https://github.com/seaweedfs/seaweedfs |
| Flowable | `flowable/flowable-rest:7.2.0` | Apache-2.0 | Workflow engine (BPMN), REST headless | Dịch vụ riêng, REST sau gateway | https://github.com/flowable/flowable-engine |
| Python official image | `python:3.12.12-alpine3.21` | PSF-2.0 (Python); các gói Alpine có giấy phép riêng | Runtime của init container deploy BPMN, chỉ dùng thư viện chuẩn | Image riêng build từ [Dockerfile](../core/workflow/Dockerfile) | https://github.com/docker-library/python |
| Python official image | `python:3.12.12-slim-bookworm` | PSF-2.0 (Python); các gói Debian có giấy phép riêng | Runtime của Data API | Image riêng build từ [Dockerfile](../data/Dockerfile) | https://github.com/docker-library/python |

## Tích hợp hệ thống khách hàng (profile: integration – đang chạy)

| Thành phần | Phiên bản | Giấy phép | Vai trò | Cách dùng | Nguồn |
|---|---|---|---|---|---|
| Snipe-IT | `snipe/snipe-it:v8.8.0` | AGPL-3.0 | Giả lập hệ thống quản lý tài sản của khách hàng | Dịch vụ riêng (profile `integration`), REST API `/api/v1`, không sửa mã (ADR-06); nạp mẫu bằng [seed.php](../core/snipeit/seed.php) | https://github.com/snipe/snipe-it |
| MariaDB | `mariadb:11.4.7` | GPL-2.0 | Cơ sở dữ liệu nội bộ của Snipe-IT | Dịch vụ riêng (profile `integration`), chỉ Snipe-IT kết nối; DX-Lab không mở cổng ra ngoài và không đọc DB trực tiếp | https://github.com/MariaDB/server |
| NATS Server | `nats:2.15.1-alpine` | Apache-2.0 | Trục sự kiện tích hợp, JetStream (#77) | Dịch vụ riêng trong profile `integration`, không mở cổng ra máy | https://github.com/nats-io/nats-server |
| Python official image | `python:3.12.12-slim-bookworm` | PSF-2.0 (Python); các gói Debian có giấy phép riêng | Runtime dịch vụ tích hợp tài sản | Image riêng build từ [Dockerfile](../integration/assets/Dockerfile) | https://github.com/docker-library/python |

## Giám sát (profile: monitoring – đang chạy)

| Thành phần | Phiên bản | Giấy phép | Vai trò | Cách dùng | Nguồn |
|---|---|---|---|---|---|
| Prometheus | `prom/prometheus:v3.15.0` | Apache-2.0 | Thu thập metric (#78) | Dịch vụ riêng trong profile `monitoring`, không mở cổng ra máy | https://github.com/prometheus/prometheus |
| Grafana | `grafana/grafana:13.2.4` | AGPL-3.0 | Dashboard giám sát (#78) | Dịch vụ riêng, bind `127.0.0.1`; dashboard JSON của đội nạp qua provisioning, không sửa mã Grafana | https://github.com/grafana/grafana |
| postgres_exporter | `prometheuscommunity/postgres-exporter:v0.20.1` | Apache-2.0 | Metric PostgreSQL bằng role `pg_monitor` | Dịch vụ riêng trong profile `monitoring` | https://github.com/prometheus-community/postgres_exporter |
| prometheus-nats-exporter | `natsio/prometheus-nats-exporter:0.20.2` | Apache-2.0 | Metric NATS, JetStream | Dịch vụ riêng trong profile `monitoring` | https://github.com/nats-io/prometheus-nats-exporter |

## Tầng 3 – Ứng dụng (đang chạy)

| Thành phần | Phiên bản | Giấy phép | Vai trò | Cách dùng | Nguồn |
|---|---|---|---|---|---|
| Nuxt | `4.5.2` | MIT | Khung ứng dụng DX-Helpdesk | Thư viện trong `app/`, ghim trong [package.json](../app/package.json) và `package-lock.json` | https://github.com/nuxt/nuxt |
| Vue | `3.5.43` | MIT | Giao diện | Thư viện, kéo theo bởi Nuxt | https://github.com/vuejs/core |
| openid-client | `6.8.8` | MIT | Luồng OIDC authorization code + PKCE, làm mới token | Thư viện phía server trong `app/server/`; kéo theo `jose`, `oauth4webapi` (MIT, cùng tác giả) | https://github.com/panva/openid-client |
| Node.js | `node:24.21.0-alpine` | MIT | Môi trường chạy ứng dụng | Image nền để dựng và chạy `app/` ([Dockerfile](../app/Dockerfile)) | https://github.com/nodejs/node |

## Tầng 2 / 3

| Thành phần | Phiên bản | Giấy phép | Vai trò | Cách dùng | Nguồn |
|---|---|---|---|---|---|
| FastAPI | `0.141.1` | MIT | HTTP Data API, OpenAPI/Swagger | Thư viện trong `data/` | https://pypi.org/project/fastapi/0.141.1/ |
| Uvicorn | `0.53.0` | BSD-3-Clause | ASGI server cho Data API | Thư viện trong `data/` | https://pypi.org/project/uvicorn/0.53.0/ |
| pg8000 | `1.31.5` | BSD-3-Clause | PostgreSQL driver thuần Python | Thư viện trong `data/` | https://pypi.org/project/pg8000/1.31.5/ |
| HTTPX | `0.28.1` | BSD-3-Clause | Gọi Flowable và Keycloak từ Data API | Thư viện trong `data/` | https://pypi.org/project/httpx/0.28.1/ |
| nats-py | `2.16.0` | Apache-2.0 | Client NATS JetStream: Data API phát, `asset-sync` nhận sự kiện (#77) | Thư viện trong `data/` và `integration/assets/` | https://github.com/nats-io/nats.py/blob/v2.16.0/LICENSE |
| PyJWT | `2.10.1` | MIT | Kiểm tra chữ ký JWT/JWKS | Thư viện trong `data/` | https://pypi.org/project/PyJWT/2.10.1/ |
| cryptography | `46.0.7` | Apache-2.0 OR BSD-3-Clause | Thuật toán RS256 cho PyJWT | Thư viện trong `data/` | https://pypi.org/project/cryptography/46.0.7/ |
| FastAPI, Uvicorn, HTTPX, PyJWT, cryptography | `0.141.1`, `0.53.0`, `0.28.1`, `2.10.1`, `46.0.7` | MIT, BSD-3-Clause, BSD-3-Clause, MIT, Apache-2.0 OR BSD-3-Clause | API tích hợp tài sản, REST Snipe-IT, xác thực token | Thư viện trong `integration/assets/`; cùng phiên bản và giấy phép với các dòng trên | [requirements.txt](../integration/assets/requirements.txt) |
| scikit-learn | _(chốt ở M3)_ | BSD-3-Clause | Phân loại, gợi ý mức ưu tiên | Thư viện trong `ai/` | https://github.com/scikit-learn/scikit-learn |
| prometheus_client (Python) | `0.26.0` | Apache-2.0 | Xuất metric từ Data API, `asset-sync` ở cổng nội bộ 9100 (#78) | Thư viện trong `data/` và `integration/assets/` | https://github.com/prometheus/client_python/blob/v0.26.0/LICENSE |
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
| pytest | 8.4.2 | MIT | Chạy test trong `tests/` (CI job `Python tests`, `make test`); không nằm trong image |
| Python 3 | 3.12+ | PSF-2.0 | Chạy smoke token, request workflow và seed trên máy phát triển |
| gitleaks | 8.24.2 | MIT | Quét secret trong CI |
| actions/checkout, actions/setup-python | v5, v6 | MIT | Bước CI trên GitHub Actions |
| actions/checkout (ghim SHA) | v5.1.0 `fbc6f39` | MIT | Lấy mã trong job dựng stack (`stack.yml`) |
| amannn/action-semantic-pull-request | v6.1.1 | MIT | Kiểm tra tiêu đề PR theo Conventional Commits |

Docker Desktop không được yêu cầu vì không phải phần mềm nguồn mở.

## Đội chọn không dùng

Bảng tham chiếu trong đề là ví dụ, đội tự chọn công nghệ. Dưới đây là các thành phần đội chọn không dùng; lý do: đội ưu tiên thành phần có giấy phép OSI để thống nhất và phù hợp mục tiêu chủ quyền số.

| Thành phần | Giấy phép | Lý do |
|---|---|---|
| HashiCorp Vault | BUSL-1.1 | BUSL-1.1; secret để trong `.env`, không commit |
| MongoDB | SSPL-1.0 (mọi bản từ 16/10/2018) | SSPL-1.0; dùng PostgreSQL thay thế |
| Redpanda | BSL 1.1 | BSL 1.1; dùng NATS thay thế |
| immudb | BUSL-1.1 | BUSL-1.1; lưu lịch sử trong PostgreSQL thay thế |
| n8n | Sustainable Use License | Sustainable Use License; dùng Flowable thay thế |
| Directus | BSL 1.1 (v10–v11), MSCL-1.0 (v12) | BSL 1.1, MSCL-1.0; dùng Data API FastAPI thay thế |
| Qwen2.5-3B, Qwen2.5-72B | Qwen Research License, Qwen License | Giấy phép riêng của mô hình; không dùng LLM |
| Llama | Llama Community License | Giấy phép riêng của mô hình; không dùng LLM |
| Gemma | Gemma Terms of Use | Giấy phép riêng của mô hình; không dùng LLM |

## Đã hủy do bỏ RAG khỏi phạm vi

| Thành phần | Giấy phép | Vai trò cũ |
|---|---|---|
| ~~Ollama~~ | MIT | Chạy LLM nội bộ |
| ~~Mô hình LLM (`qwen2.5:1.5b`)~~ | Apache-2.0 | RAG hỏi đáp tài liệu |
| ~~pgvector~~ | PostgreSQL | Tìm kiếm véc-tơ cho RAG |

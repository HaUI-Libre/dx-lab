<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Quyết định giấy phép

Tài liệu ghi giấy phép của DX-Lab, lý do chọn, quyền và nghĩa vụ của người dùng, và
kết quả rà soát giấy phép của từng thành phần bên ngoài. Bảng thành phần đang dùng
nằm ở [dependencies.md](dependencies.md); tài liệu này giải thích vì sao bảng đó
trông như vậy.

Ngày rà soát: 2026-10-17.

## 1. Giấy phép của dự án

Toàn bộ mã nguồn, cấu hình và tài liệu do đội viết phát hành theo
**Apache License 2.0** (SPDX: `Apache-2.0`). Toàn văn ở [LICENSE](../LICENSE) và
[LICENSES/Apache-2.0.txt](../LICENSES/Apache-2.0.txt); thông báo bản quyền ở
[NOTICE](../NOTICE).

### Vì sao chọn Apache-2.0

1. **Được OSI chấp thuận**, đáp ứng yêu cầu của BTC về giấy phép nguồn mở.
2. **Cấp quyền sáng chế rõ ràng** (mục 3). Người đóng góp cấp quyền dùng mọi bằng
   sáng chế liên quan tới phần mình đóng góp; ai kiện vi phạm sáng chế thì mất quyền
   đó. MIT và BSD không có điều khoản này.
3. **Cùng giấy phép với lõi Tầng 1.** Keycloak, Apache APISIX, SeaweedFS, Flowable,
   NATS, Prometheus đều dùng Apache-2.0. Không phát sinh câu hỏi tương thích, và đội
   dùng chung quy ước `NOTICE` với các dự án đó.
4. **Cho phép tích hợp với hệ thống của khách hàng.** Mục tiêu DX-OS là một trường
   hay đơn vị khác lấy về, gắn vào phần mềm sẵn có của họ (kể cả phần mềm độc quyền)
   mà không bị buộc mở mã phần của họ. Giấy phép dễ dãi (permissive) đáp ứng được.

### Các phương án đã so sánh

| Giấy phép | Lý do không chọn |
|---|---|
| MIT, BSD-3-Clause | Ngắn gọn nhưng không có điều khoản sáng chế và không có cơ chế `NOTICE` |
| GPL-3.0 | Copyleft mạnh: bên tích hợp phải phát hành mã theo GPL khi phân phối, cản trở khách hàng gắn DX-OS vào hệ thống của họ |
| AGPL-3.0 | Như GPL-3.0, thêm nghĩa vụ công bố mã khi cung cấp qua mạng. Phù hợp với sản phẩm muốn chống "đóng mã qua SaaS", không phù hợp với nền tảng để người khác tích hợp |
| MPL-2.0 | Copyleft theo từng tệp, cân bằng nhưng phức tạp hơn mà không mang lại lợi ích gì thêm cho đội |

Đánh đổi đã chấp nhận: người khác có thể lấy mã của đội, sửa và không công bố phần
sửa. Đội chấp nhận vì ưu tiên việc tái sử dụng.

## 2. Quyền và nghĩa vụ của người dùng

Tóm tắt Apache-2.0 để tham khảo; khi có khác biệt, văn bản trong [LICENSE](../LICENSE)
có hiệu lực.

**Được phép:** dùng cho mọi mục đích, kể cả thương mại; sao chép, sửa đổi, phân phối
bản gốc hoặc bản sửa đổi, ở dạng mã nguồn hoặc dạng đã đóng gói; cấp phép lại phần
sửa đổi của mình theo điều khoản khác.

**Nghĩa vụ khi phân phối lại (mục 4):**

- Kèm bản sao giấy phép Apache-2.0.
- Ghi rõ trong các tệp đã sửa là tệp đó đã bị thay đổi.
- Giữ nguyên các thông báo bản quyền, sáng chế, nhãn hiệu có trong mã nguồn.
- Kèm nội dung tệp `NOTICE` nếu có.

**Không được:** dùng tên, nhãn hiệu của dự án hay của HaUI để quảng bá sản phẩm phái
sinh (mục 6). Phần mềm cung cấp "nguyên trạng", không có bảo hành (mục 7, 8).

## 3. Cách áp dụng trong repo

| Cơ chế | Vị trí | Mục đích |
|---|---|---|
| Header SPDX 2 dòng | Đầu mọi tệp mã, cấu hình, tài liệu | Mỗi tệp tự mang thông tin bản quyền và giấy phép |
| Tệp `<tên-tệp>.license` | Cạnh tệp JSON, ảnh | Khai báo cho tệp không chứa được comment. Không dùng `REUSE.toml` để giấy phép nằm ngay cạnh tệp, ai mở thư mục cũng thấy |
| `LICENSES/` | Gốc repo | Toàn văn mọi giấy phép được dùng, theo chuẩn REUSE: Apache-2.0 cho mã của đội, CC-BY-4.0 cho `CODE_OF_CONDUCT.md` |
| `NOTICE` | Gốc repo | Thông báo bản quyền và ghi nhận thành phần bên thứ ba |
| `reuse lint` | CI, `make check` | Chặn PR có tệp thiếu thông tin giấy phép |
| gitleaks | CI | Chặn secret lọt vào lịch sử |

Chuẩn áp dụng: [REUSE Specification 3.3](https://reuse.software/spec-3.3/).

## 4. Phạm vi áp dụng giấy phép

- **Mã nguồn trong repo:** Mã nguồn và cấu hình của đội theo Apache-2.0. Nội dung của bên thứ ba (ví dụ CODE_OF_CONDUCT.md theo CC-BY-4.0) giữ giấy phép riêng, được khai trong NOTICE và header SPDX của tệp.
- **Dịch vụ chạy riêng:** Dịch vụ chạy riêng không tính vào giấy phép mã nguồn của dự án, nhưng đội vẫn chọn thành phần OSI để thống nhất và vì chủ quyền số. Các dịch vụ này được ghi nhận đầy đủ trong [dependencies.md](dependencies.md) và [NOTICE](../NOTICE).
- **Không sửa mã nguồn thư viện bên ngoài trong repo.**

## 5. Quy tắc chọn thành phần bên ngoài

1. Phần lõi chỉ dùng giấy phép được OSI chấp thuận.
2. Giấy phép copyleft mạnh (GPL, AGPL) chỉ chấp nhận khi thành phần chạy như
   **dịch vụ riêng**: container riêng, giao tiếp qua HTTP/SQL/giao thức mạng, không
   liên kết vào mã của đội, đội không sửa mã nguồn của nó. Khi đó nghĩa vụ copyleft
   gắn với bản thân thành phần, không lan sang mã Apache-2.0 của đội. Nếu sau này
   cần sửa mã của thành phần AGPL thì phải công bố phần sửa theo AGPL.
3. Với các thành phần có giấy phép "source available" (BSL, SSPL, Sustainable Use, RSAL, Elastic)
   hay giấy phép riêng của mô hình AI (Llama, Gemma, Qwen Research), đội chọn không dùng;
   lý do: đội ưu tiên thành phần có giấy phép OSI để thống nhất và phù hợp mục tiêu chủ quyền số.
4. **Kiểm tra theo đúng phiên bản.** Giấy phép có thể đổi giữa các phiên bản, nên đọc
   tệp giấy phép tại đúng tag sẽ dùng và ghim tag đó trong `docker-compose.yml`.
   Không dùng tag trôi như `latest`, `alpine`, `4.0`.
5. Thành phần mới phải được ghi vào [dependencies.md](dependencies.md) và bảng dưới
   đây trong cùng PR thêm nó.

## 6. Rà soát giấy phép từng thành phần

Cột "Phiên bản kiểm tra" là tag đã đọc tệp giấy phép. Với thành phần chưa tích hợp,
đó là bản phát hành mới nhất tại ngày rà soát; phải kiểm tra lại khi chốt tag.

### Đang dùng (Tầng 1)

| Thành phần | Phiên bản kiểm tra | Giấy phép | OSI | Cách dùng | Nguồn |
|---|---|---|---|---|---|
| Keycloak | 26.8.0 | Apache-2.0 | Có | Dịch vụ riêng, OIDC | [LICENSE.txt](https://github.com/keycloak/keycloak/blob/26.8.0/LICENSE.txt) |
| Apache APISIX | 3.19.0 | Apache-2.0 | Có | Dịch vụ riêng; plugin `dxlab-roles` của đội nạp qua `extra_lua_path`, không sửa mã APISIX | [LICENSE](https://github.com/apache/apisix/blob/3.19.0/LICENSE) |
| PostgreSQL | 18.6 | PostgreSQL | Có | Dịch vụ riêng, SQL | [postgresql.org/about/licence](https://www.postgresql.org/about/licence/) |
| SeaweedFS | 4.48 | Apache-2.0 | Có | Dịch vụ riêng, HTTP filer | [LICENSE](https://github.com/seaweedfs/seaweedfs/blob/4.48/LICENSE) |
| Flowable REST | 7.2.0 | Apache-2.0 | Có | Dịch vụ riêng, REST | [LICENSE](https://github.com/flowable/flowable-engine/blob/flowable-7.2.0/LICENSE) |
| PostGIS | 3.6.4 | GPL-2.0-or-later | Có | Extension trong `dxdata`, gọi qua SQL; mã của đội không liên kết với PostGIS (#76) | [LICENSE.TXT](https://github.com/postgis/postgis/blob/3.6.4/LICENSE.TXT) |
| docker-postgis (Dockerfile của image) | commit 148ce95 | MIT | Có | Image `postgis/postgis:18-3.6-alpine`, ghim digest | [LICENSE](https://github.com/postgis/docker-postgis/blob/148ce95110aaf09bd6db17283e12e5f4f4c510e8/LICENSE) |
| Python (image chính thức) | 3.12.12 | PSF-2.0 | Có | Image nền `python:3.12.12-alpine3.21` (deploy BPMN), `python:3.12.12-slim-bookworm` (Data API, asset-sync) | [LICENSE](https://github.com/python/cpython/blob/v3.12.12/LICENSE) |

### Đang dùng (Tầng 3)

| Thành phần | Phiên bản kiểm tra | Giấy phép | OSI | Cách dùng | Nguồn |
|---|---|---|---|---|---|
| Nuxt | v4.5.2 | MIT | Có | Khung ứng dụng trong `app/` | [LICENSE](https://github.com/nuxt/nuxt/blob/v4.5.2/LICENSE) |
| Vue | v3.5.43 | MIT | Có | Thư viện giao diện | [LICENSE](https://github.com/vuejs/core/blob/v3.5.43/LICENSE) |
| openid-client | v6.8.8 | MIT | Có | Thư viện OIDC phía server Nuxt | [LICENSE.md](https://github.com/panva/openid-client/blob/v6.8.8/LICENSE.md) |
| Node.js | v24.21.0 | MIT | Có | Image nền `node:24.21.0-alpine` | [LICENSE](https://github.com/nodejs/node/blob/v24.21.0/LICENSE) |

Quét trường `license` của toàn bộ 679 gói trong `app/package-lock.json` (18/10/2026):
574 MIT, 36 ISC, 16 Apache-2.0, 14 BlueOak-1.0.0, 12 MPL-2.0, 11 BSD-2-Clause,
9 BSD-3-Clause, đều được OSI chấp thuận; không gói nào thiếu thông tin giấy phép.
Ngoài OSI chỉ có dữ liệu dùng lúc build: `caniuse-lite` (CC-BY-4.0), `mdn-data` và
`@speed-highlight/core` (CC0-1.0); `type-fest` (MIT OR CC0-1.0) và `node-forge`
(BSD-3-Clause OR GPL-2.0) dùng nhánh OSI. Bản chạy trong image (`.output/server`)
chỉ chứa 25 gói MIT, BSD-2-Clause, BSD-3-Clause; các gói kể trên không nằm trong đó.

### Đang dùng (Tích hợp hệ thống khách hàng, profile: integration)

| Thành phần | Phiên bản kiểm tra | Giấy phép | OSI | Cách dùng | Nguồn |
|---|---|---|---|---|---|
| Snipe-IT | v8.8.0 | AGPL-3.0 | Có | Dịch vụ riêng giả lập hệ thống tài sản của khách hàng, gọi REST API `/api/v1`, không sửa mã (ADR-06) | [LICENSE](https://github.com/grokability/snipe-it/blob/v8.8.0/LICENSE) |
| MariaDB | mariadb-11.4.7 | GPL-2.0 | Có | Dịch vụ riêng, database của Snipe-IT theo compose chính thức; DX-Lab không mở cổng và không đọc DB trực tiếp | [COPYING](https://github.com/MariaDB/server/blob/mariadb-11.4.7/COPYING) |

### Đang dùng (Tầng 2: Data API, dịch vụ tích hợp)

| Thành phần | Phiên bản kiểm tra | Giấy phép | OSI | Cách dùng | Nguồn |
|---|---|---|---|---|---|
| FastAPI | 0.141.1 | MIT | Có | Thư viện trong `data/`, `integration/assets/` | [LICENSE](https://github.com/fastapi/fastapi/blob/0.141.1/LICENSE) |
| Uvicorn | 0.53.0 | BSD-3-Clause | Có | ASGI server | [LICENSE.md](https://github.com/encode/uvicorn/blob/0.53.0/LICENSE.md) |
| pg8000 | 1.31.5 | BSD-3-Clause | Có | Driver PostgreSQL của Data API | LICENSE trong [gói nguồn 1.31.5 trên PyPI](https://pypi.org/project/pg8000/1.31.5/#files); mã nguồn chuyển sang [Codeberg](https://codeberg.org/tlocke/pg8000) |
| HTTPX | 0.28.1 | BSD-3-Clause | Có | Gọi Flowable, Keycloak, Snipe-IT | [LICENSE.md](https://github.com/encode/httpx/blob/0.28.1/LICENSE.md) |
| PyJWT | 2.10.1 | MIT | Có | Kiểm tra JWT bằng JWKS | [LICENSE](https://github.com/jpadilla/pyjwt/blob/2.10.1/LICENSE) |
| cryptography | 46.0.7 | Apache-2.0 OR BSD-3-Clause | Có | RS256 cho PyJWT; dùng theo nhánh Apache-2.0 | [LICENSE](https://github.com/pyca/cryptography/blob/46.0.7/LICENSE) |
| nats-py | v2.16.0 | Apache-2.0 | Có | Client JetStream (#77) | [LICENSE](https://github.com/nats-io/nats.py/blob/v2.16.0/LICENSE) |
| prometheus_client (Python) | v0.26.0 | Apache-2.0 | Có | Thư viện trong Data API, dịch vụ tích hợp; metric ở cổng nội bộ 9100 (#78) | [LICENSE](https://github.com/prometheus/client_python/blob/v0.26.0/LICENSE) |

### Đang dùng (Trục sự kiện, profile: integration)

| Thành phần | Phiên bản kiểm tra | Giấy phép | OSI | Cách dùng | Nguồn |
|---|---|---|---|---|---|
| NATS Server | v2.15.1 | Apache-2.0 | Có | Dịch vụ riêng, JetStream, không mở cổng ra máy (#77) | [LICENSE](https://github.com/nats-io/nats-server/blob/v2.15.1/LICENSE) |

### Đang dùng (Giám sát, profile: monitoring)

| Thành phần | Phiên bản kiểm tra | Giấy phép | OSI | Cách dùng | Nguồn |
|---|---|---|---|---|---|
| Prometheus | v3.15.0 | Apache-2.0 | Có | Dịch vụ riêng, thu thập metric | [LICENSE](https://github.com/prometheus/prometheus/blob/v3.15.0/LICENSE) |
| Grafana | v13.2.4 | AGPL-3.0 | Có | Dịch vụ riêng; dashboard của đội là tệp JSON nạp qua provisioning, không sửa mã Grafana | [LICENSE](https://github.com/grafana/grafana/blob/v13.2.4/LICENSE) |
| postgres_exporter | v0.20.1 | Apache-2.0 | Có | Dịch vụ riêng, metric PostgreSQL | [LICENSE](https://github.com/prometheus-community/postgres_exporter/blob/v0.20.1/LICENSE) |
| prometheus-nats-exporter | v0.20.2 | Apache-2.0 | Có | Dịch vụ riêng, metric NATS | [LICENSE](https://github.com/nats-io/prometheus-nats-exporter/blob/v0.20.2/LICENSE) |

### Dự kiến

| Thành phần | Phiên bản kiểm tra | Giấy phép | OSI | Cách dùng dự kiến | Nguồn |
|---|---|---|---|---|---|
| scikit-learn | 1.9.1 | BSD-3-Clause | Có | Thư viện trong dịch vụ phân loại ưu tiên | [COPYING](https://github.com/scikit-learn/scikit-learn/blob/1.9.1/COPYING) |
| Leaflet | v1.9.4 | BSD-2-Clause | Có | Thư viện bản đồ đóng gói trong giao diện; giữ thông báo bản quyền trong bản build | [LICENSE](https://github.com/Leaflet/Leaflet/blob/v1.9.4/LICENSE) |

### Nội dung bên thứ ba nằm trong repo

| Tệp | Nguồn | Giấy phép | Ghi chú |
|---|---|---|---|
| `CODE_OF_CONDUCT.md` | Contributor Covenant 2.1, bản tiếng Việt ([code_of_conduct.vi.md](https://github.com/EthicalSource/contributor_covenant/blob/e0324b3cc9df5f3a62b6027157d8c2da5e0f6d68/content/version/2/1/code_of_conduct.vi.md)) | CC-BY-4.0 ([LICENSE.md tại 91532d80ea](https://github.com/EthicalSource/contributor_covenant/blob/91532d80ea/LICENSE.md)) | Chỉ sửa thông tin liên hệ. Bản 3.0 dùng CC BY-SA 4.0 nên không chọn. Mã của website Contributor Covenant theo Hippocratic License, không áp dụng cho văn bản |

### Dữ liệu

| Nguồn | Giấy phép | Nghĩa vụ | Nguồn |
|---|---|---|---|
| OpenStreetMap | ODbL 1.0 (Open Data Commons) | Hiển thị ghi công "© OpenStreetMap contributors" và nêu rõ dữ liệu theo ODbL. Chính sách dùng tile server cần kiểm tra khi chọn nguồn tile | [openstreetmap.org/copyright](https://www.openstreetmap.org/copyright) |

### Công cụ phát triển (không phân phối kèm sản phẩm)

| Công cụ | Phiên bản kiểm tra | Giấy phép | Nguồn |
|---|---|---|---|
| Docker Engine (Moby) | docker-v29.9.1 | Apache-2.0 | [LICENSE](https://github.com/moby/moby/blob/docker-v29.9.1/LICENSE) |
| Docker Compose | v5.6.0 | Apache-2.0 | [LICENSE](https://github.com/docker/compose/blob/v5.6.0/LICENSE) |
| reuse | 6.2.0 | GPL-3.0-or-later (một phần Apache-2.0, CC0-1.0, CC-BY-SA-4.0) | [pyproject.toml](https://github.com/fsfe/reuse-tool/blob/v6.2.0/pyproject.toml) |
| gitleaks | 8.24.2 | MIT | [LICENSE](https://github.com/gitleaks/gitleaks/blob/v8.24.2/LICENSE) |
| actions/checkout, actions/setup-python | v5, v6 | MIT | [checkout](https://github.com/actions/checkout/blob/main/LICENSE), [setup-python](https://github.com/actions/setup-python/blob/main/LICENSE) |

reuse dùng GPL nhưng chỉ chạy trong CI và trên máy lập trình viên, không được phân
phối cùng sản phẩm nên không ảnh hưởng tới giấy phép của đội.

**Docker Desktop không được yêu cầu.** Docker Desktop cấp phép theo Docker
Subscription Service Agreement, không phải nguồn mở
([docs.docker.com](https://docs.docker.com/subscription/desktop-license/)). README
hướng dẫn dùng Docker Engine và Compose plugin, trên Windows thì chạy qua WSL2.

## 7. Minh chứng: giấy phép đổi theo phiên bản

Ba trường hợp dưới đây cho thấy vì sao phải đọc giấy phép tại đúng tag, không dựa vào
tên dự án hay thông tin cũ.

**MongoDB với tag `mongo:4.0`.** Nhiều tài liệu ghi MongoDB 4.0 là AGPL-3.0. Theo FAQ
của MongoDB, mọi bản phát hành từ 16/10/2018, *kể cả bản vá cho dòng cũ*, theo SSPL.
Tag `4.0` trỏ tới bản vá mới nhất; tệp giấy phép tại `r4.0.28` là
"Server Side Public License, Version 1"
([LICENSE-Community.txt](https://github.com/mongodb/mongo/blob/r4.0.28/LICENSE-Community.txt),
[FAQ](https://www.mongodb.com/legal/licensing/server-side-public-license/faq)).
SSPL không được OSI chấp thuận.

**Redis với tag `redis:alpine`.** Redis 7.2 trở về trước theo BSD-3-Clause; 7.4 theo
RSALv2 hoặc SSPLv1; từ Redis 8 cho chọn RSALv2, SSPLv1 hoặc AGPLv3
([redis.io/legal/licenses](https://redis.io/legal/licenses/),
[LICENSE.txt tại 8.10.2](https://github.com/redis/redis/blob/8.10.2/LICENSE.txt)).
Tag `alpine` là tag trôi, hiện trỏ tới Redis 8, nên ghi "BSD-3-Clause" cho tag này là
sai.

**Directus.** Bản v10 và v11 theo Business Source License 1.1; từ v12 chuyển sang
Monospace Sustainable Core License 1.0
([license tại v11.9.0](https://github.com/directus/directus/blob/v11.9.0/license),
[license tại v12.5.0](https://github.com/directus/directus/blob/v12.5.0/license)).
Cả hai đều không phải giấy phép OSI.

## 8. Đội chọn không dùng

Bảng tham chiếu trong đề là ví dụ, đội tự chọn công nghệ
([đề thi](https://www.vfossa.vn/tin-tuc/de-thi-phan-mem-nguon-mo-olp-2026-798.html)).
Với Vault, MongoDB, n8n, Redpanda và immudb nằm trong bảng tham khảo đó, đội chọn không dùng;
lý do: đội ưu tiên thành phần có giấy phép OSI để thống nhất và phù hợp mục tiêu chủ quyền số.
Ánh xạ 7 lớp: [architecture.md](architecture.md) mục 2.

| Thành phần | Phiên bản kiểm tra | Giấy phép | Thay bằng | Nguồn |
|---|---|---|---|---|
| HashiCorp Vault | v2.2.0 | BUSL-1.1 | Secret để trong `.env`, không commit | [LICENSE](https://github.com/hashicorp/vault/blob/v2.2.0/LICENSE) |
| MongoDB | r4.0.28 | SSPL-1.0 | PostgreSQL | Xem mục 7 |
| Redpanda | v26.2.2 | BSL 1.1 (một phần RCL) | NATS | [licenses/bsl.md](https://github.com/redpanda-data/redpanda/blob/v26.2.2/licenses/bsl.md) |
| immudb | v1.11.2 | BUSL-1.1 | Lịch sử thay đổi lưu trong PostgreSQL | [LICENSE](https://github.com/codenotary/immudb/blob/v1.11.2/LICENSE) |
| n8n | 2.43.7 | Sustainable Use License | Flowable | [LICENSE.md](https://github.com/n8n-io/n8n/blob/n8n@2.43.7/LICENSE.md) |
| Directus | v11.9.0, v12.5.0 | BSL 1.1, MSCL-1.0 | Data API FastAPI | Xem mục 7 |
| Qwen2.5-3B-Instruct | bản trên Hugging Face | Qwen Research License | Không dùng LLM | [LICENSE](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/blob/main/LICENSE) |
| Qwen2.5-72B-Instruct | bản trên Hugging Face | Qwen License | Không dùng LLM | [LICENSE](https://huggingface.co/Qwen/Qwen2.5-72B-Instruct/blob/main/LICENSE) |
| Llama 3.1 | Llama-3.1-8B-Instruct | Llama 3.1 Community License | Không dùng LLM | [Hugging Face](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct) |
| Gemma 2 | gemma-2-2b-it | Gemma Terms of Use | Không dùng LLM | [Hugging Face](https://huggingface.co/google/gemma-2-2b-it) |

### Bỏ vì thay đổi phạm vi, không vì giấy phép

RAG hỏi đáp tài liệu bị bỏ khỏi phạm vi. Các thành phần đi kèm không còn dùng:

| Thành phần | Giấy phép | Ghi chú |
|---|---|---|
| Ollama | MIT | Chạy LLM nội bộ cho RAG |
| Qwen2.5-1.5B-Instruct | Apache-2.0 | Từng ghi trong `.env.example` ([LICENSE](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct/blob/main/LICENSE)) |
| pgvector | PostgreSQL | Tìm kiếm véc-tơ cho RAG |

Phần trí tuệ (I) còn lại là phân loại và gợi ý mức ưu tiên bằng scikit-learn, có
fallback rule-based.

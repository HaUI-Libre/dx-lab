<!--
SPDX-FileCopyrightText: 2026 HaUI-Libre DX-Lab contributors
SPDX-License-Identifier: Apache-2.0
-->

# Changelog

Mọi thay đổi đáng chú ý của dự án được ghi tại đây.

Định dạng theo [Keep a Changelog](https://keepachangelog.com/vi/1.1.0/),
đánh số phiên bản theo [Semantic Versioning](https://semver.org/lang/vi/).

## [Unreleased]

### Added
- Cổng thông tin [H] (`/portal`): xem hồ sơ cá nhân, nhóm và đơn vị 3 cơ sở, danh sách tài liệu hướng dẫn theo vai trò người dùng, tải lên, xem và tải về qua `/api/files` kết nối SeaweedFS (#25).
- Init container `workflow-deploy` deploy BPMN qua REST nội bộ khi `make up`, chỉ tạo
  version mới khi nội dung BPMN đổi; route workflow kiểm thử chỉ cho `ROLE_ADMIN`;
  `docs/workflow-api.sh` chạy ba nhánh hoàn thành, từ chối, mở lại qua gateway (#88).
- Realm demo: user attribute `co_so` chỉ admin sửa, mapper đưa vào claim `co_so` của
  access token; 10 tài khoản demo cho 3 cơ sở với UUID cố định; `make smoke` kiểm tra
  UUID, vai trò và `co_so` của từng tài khoản (#87).
- BPMN `dxlabHelpdeskRepair` trong `core/workflow/`: tiếp nhận, phân công, xử lý,
  nghiệm thu, nhánh từ chối và mở lại bắt buộc có lý do; sơ đồ
  `docs/images/helpdesk-workflow.svg` (#85).
- Dữ liệu mẫu 3 cơ sở HaUI trong `data/samples/`: cây vị trí, tài sản và người dùng cho
  Snipe-IT, ticket ở đủ trạng thái kèm lịch sử, 160 mẫu huấn luyện phân loại;
  `make seed` nạp lặp an toàn và thoát mã lỗi khi thất bại (#81, #83).
- Ứng dụng DX-Helpdesk (Nuxt 4.5.2) trong `app/`: đăng nhập, đăng xuất SSO theo mô hình
  BFF (server Nuxt giữ token, trình duyệt chỉ có cookie phiên), trang tài khoản hiện
  tên, vai trò, cơ sở lấy qua `GET /api/me`; Dockerfile, service `app` trong compose,
  `make smoke` có bước đăng nhập qua app (#24).
- `docs/architecture.md`: tích hợp hệ thống tài sản của khách hàng (Snipe-IT), trục sự
  kiện NATS, định tuyến theo cơ sở, giám sát, profile Compose, bảng ánh xạ 7 lớp công
  nghệ của đề; ảnh `docs/images/integration-architecture.svg` (#67).
- `docs/usecases.md`: kịch bản theo hướng tích hợp tài sản, cơ sở `co_so`, nhánh mở lại
  ở bước nghiệm thu (#67).
- `CODE_OF_CONDUCT.md` theo Contributor Covenant 2.1 bản tiếng Việt (CC-BY-4.0) (#63).
- CONTRIBUTING: quy tắc viết commit, quy trình PR (Draft, rebase, squash), mục bản quyền
  đóng góp theo DCO, nguồn tham khảo từ Kubernetes, Keycloak, APISIX, Airflow (#63).
- Mẫu PR: mục "Ghi chú cho người review" và "Công cụ hỗ trợ đã dùng" (#63).
- CI kiểm tra tiêu đề PR theo Conventional Commits (#63).
- `docs/license-decision.md`: lý do chọn Apache-2.0, quyền và nghĩa vụ người dùng,
  rà soát giấy phép từng thành phần theo phiên bản kèm nguồn (#61).
- `NOTICE` theo chuẩn Apache-2.0, có phần tiếng Việt và bảng thành phần bên thứ ba (#61).
- `LICENSES/Apache-2.0.txt` theo REUSE Specification 3.3; tệp `.license` đi kèm cho
  ảnh SVG trong `docs/images/` (#61).
- README: mục Giấy phép nêu mục đích giấy phép; hướng dẫn chạy trên Windows qua WSL2 (#61).

### Changed
- Cập nhật cách diễn đạt về phạm vi áp dụng giấy phép và bảng tham chiếu công nghệ trong tài liệu (#92).
- CI và `make check` kiểm tra giấy phép bằng `reuse lint` thay cho
  `scripts/check_spdx.sh` (#61).
- `docs/dependencies.md`: thêm cột "Cách dùng", thành phần dự kiến của hướng tích hợp
  tài sản, danh sách đã cân nhắc nhưng không dùng (#61).
- README yêu cầu Docker Engine và Compose plugin, không cần Docker Desktop (#61).
- Redirect URI của client `dxlab-app` và CORS ở gateway lấy theo `APP_PORT`, không ghim
  `localhost:3000` (#24).
- `/api/me` trả thêm `co_so` khi token có claim này (#24).

### Removed
- RAG, Ollama, pgvector khỏi phạm vi; bỏ `OLLAMA_MODEL`, `AI_FALLBACK_RULE_BASED`
  khỏi `.env.example` (#61).
- `scripts/check_spdx.sh` (#61).

### Fixed
- Data API không gọi được Flowable: `DATA_WORKFLOW_KEY` chưa có trong `nginx_config.envs`
  của APISIX nên route `workflow-data` luôn trả 403 và mọi bước chuyển trạng thái trả 503.
  `make env` sinh khoá ngẫu nhiên thay cho `changeme` (trừ mật khẩu tài khoản demo);
  `make up` dừng khi `DATA_WORKFLOW_KEY` còn là `changeme`; `make smoke` chạy vòng đời
  ticket qua Data API, gồm nhánh mở lại và từ chối (#98).
- Gateway kiểm tra quyền theo đường dẫn trong `/api/files`: `guides/admin/` chỉ admin đọc,
  `guides/technician/` chỉ kỹ thuật viên, quản lý, admin đọc; ghi và xoá `guides/`, `portal/`
  chỉ quản lý và admin. Trước đây mọi vai trò đọc, ghi được mọi tệp, kể cả metadata phân
  quyền của portal. Chặn `..` và `%2e` trong request gốc (#95).
- Keycloak 26.8 không import được realm trên volume trống vì user profile đặt
  `unmanagedAttributePolicy` là `DISABLED`, giá trị không hợp lệ; bỏ trường này (#89).
- `docs/workflow-api.sh` lỗi khi sắp xếp lịch sử task vì Flowable 7 sinh ID task dạng
  UUID; sắp xếp theo thời gian bắt đầu và kết thúc (#89).
- Gateway trả `Content-Type: application/json` cho `/api/me` và các lỗi 400, 403, 503
  do gateway tự sinh; trước đây là `text/plain` (#24).

## [0.1.0] - 2026-10-14

### Added
- Khung repository: cấu trúc thư mục, README, CONTRIBUTING, CHANGELOG.
- Mẫu Issue/Pull Request, CODEOWNERS.
- CI: kiểm tra SPDX header và quét secret bằng gitleaks.
- `.env.example`, Makefile, bảng dependency/license.
- `docs/usecases.md`: đặc tả nghiệp vụ DX-Helpdesk (vai trò, loại sự cố, trạng thái,
  kịch bản), chuyển từ bản .docx (#9).
- Docker Compose: PostgreSQL 18 với volume, healthcheck và script tạo database
  riêng cho Keycloak, Flowable, Data API (#11).
- Keycloak 26.8: realm `dxlab` tự import, client OIDC `dxlab-app`, 4 realm role
  theo M1.3 và tài khoản demo cho mỗi vai trò; mật khẩu lấy từ `.env` (#12).
- APISIX 3.19 chạy standalone: route `/api/me`, `/api/data`, `/api/workflow`,
  `/api/files`, `/api/ai`; xác thực token Keycloak bằng JWKS, plugin `dxlab-roles`
  kiểm tra vai trò; `make smoke` kiểm tra 401/200/403 (#13).
- `docs/architecture.md`: kiến trúc 3 tầng, ánh xạ không gian H-P-D-I, ranh giới mạng,
  6 luồng gọi dịch vụ (sequence diagram), bảng hợp đồng API và 5 quyết định kiến trúc
  then chốt (ADR); bổ sung ảnh sơ đồ vector trong `docs/images/` (#10).
- SeaweedFS 4.48 lưu tệp trong bucket `documents`; tải lên/tải về qua
  `/api/files` của gateway, chặn liệt kê thư mục và lệnh quản trị của filer (#14).
- Flowable REST chạy headless trên database `flowable`; gateway công bố
  `GET /api/workflow/repository/process-definitions` (#15).
- `data/schema.sql` và `data/openapi.yaml`: schema ticket, tệp đính kèm, lịch sử và
  hợp đồng Data API dự kiến (#16).

### Changed
- CI dùng `actions/checkout@v5` và ghim `ubuntu-24.04`.

[Unreleased]: https://github.com/HaUI-Libre/dx-lab/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/HaUI-Libre/dx-lab/releases/tag/v0.1.0


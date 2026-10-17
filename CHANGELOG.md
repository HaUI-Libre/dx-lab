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
- CI và `make check` kiểm tra giấy phép bằng `reuse lint` thay cho
  `scripts/check_spdx.sh` (#61).
- `docs/dependencies.md`: thêm cột "Cách dùng", thành phần dự kiến của hướng tích hợp
  tài sản, danh sách đã cân nhắc nhưng không dùng (#61).
- README yêu cầu Docker Engine và Compose plugin, không cần Docker Desktop (#61).

### Removed
- RAG, Ollama, pgvector khỏi phạm vi; bỏ `OLLAMA_MODEL`, `AI_FALLBACK_RULE_BASED`
  khỏi `.env.example` (#61).
- `scripts/check_spdx.sh` (#61).

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


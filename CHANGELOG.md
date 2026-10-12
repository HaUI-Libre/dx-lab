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
- Khung repository: cấu trúc thư mục, README, CONTRIBUTING, CHANGELOG.
- Mẫu Issue/Pull Request, CODEOWNERS.
- CI: kiểm tra SPDX header và quét secret bằng gitleaks.
- `.env.example`, Makefile, bảng dependency/license.
- Docker Compose: PostgreSQL 18 với volume, healthcheck và script tạo database
  riêng cho Keycloak, Flowable, Data API (#11).
- Keycloak 26.8: realm `dxlab` tự import, client OIDC `dxlab-app`, 4 realm role
  theo M1.3 và tài khoản demo cho mỗi vai trò; mật khẩu lấy từ `.env` (#12).
